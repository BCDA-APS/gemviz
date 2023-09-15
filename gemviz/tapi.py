"""
TAPI: Local support for the tiled API & data structures.

.. autosummary:

    ~connect_tiled_server
    ~get_md
    ~get_tiled_runs
    ~QueryTimeSince
    ~QueryTimeUntil
    ~run_description_table
    ~run_summary
    ~run_summary_table
    ~stream_data_field_pv
    ~stream_data_field_shape
    ~stream_data_field_units
    ~stream_data_fields
    ~TiledServerError
"""

import datetime

import tiled
import tiled.queries
from httpx import HTTPStatusError

from . import utils


class TiledServerError(RuntimeError):
    """An error from the tiled server."""


def connect_tiled_server(uri):
    from tiled.client import from_uri

    # leave out "dask" and get numpy by default
    # https://examples.dask.org/array.html
    # > Call .compute() when you want your result as a NumPy array.
    client = from_uri(uri, "dask")
    return client


def get_md(parent, doc, key, default=None):
    """Cautiously, get metadata from tiled object by document and key."""
    return (parent.metadata.get(doc) or {}).get(key) or default


def get_tiled_slice(cat, offset, size, ascending=True):
    end = offset + size
    key_gen = cat.keys()

    try:
        return key_gen[offset:end]
    except HTTPStatusError as exc:
        # fmt: off
        # logger.error("HTTPStatusError: %s", exc)
        raise TiledServerError(
            f"{exc.response.reason_phrase}"
            f" ({exc.response.status_code})"
            "  Adjust filters to reduce the catalog size."
        )
        # fmt: on


def QueryTimeSince(isotime):
    """Tiled client query: all runs since given date/time."""
    return tiled.queries.Key("time") >= utils.iso2ts(isotime)


def QueryTimeUntil(isotime):
    """Tiled client query: all runs until given date/time."""
    return tiled.queries.Key("time") <= utils.iso2ts(isotime)


def get_run(uri=None, catalog="training", reference=None):
    """Get referenced run from tiled server catalog."""
    from gemviz.tapi import connect_tiled_server
    from gemviz.tapi import get_tiled_runs

    uri = uri or "http://localhost:8020"
    client = connect_tiled_server(uri)
    cat = get_tiled_runs(client[catalog], plan_name="scan")
    reference = reference or -1
    uid = reference if isinstance(reference, str) else cat.keys()[reference]
    run = cat[uid]
    return run


def get_tiled_runs(cat, since=None, until=None, text=[], text_case=[], **keys):
    """
    Return a new catalog, filtered by search terms.

    Runs will be selected with start time `>=since` and `< until`.
    If either is `None`, then the corresponding filter will not be
    applied.

    Parameters

    `cat` obj :
        This is the catalog to be searched.
        `Node` object returned by tiled.client.
    `since` str :
        Earliest start date (& time), in ISO8601 format.
    `until` str :
        Latest start date (& time), in ISO8601 format.
    `text` [str] :
        List of full text searches.  Not sensitive to case.
    `text_case` [str] :
        List of full text searches.  Case sensitive.
    `keys` dict :
        Dictionary of metadata keys and values to be matched.
    """
    if since is not None:
        cat = cat.search(QueryTimeSince(since))
    if until is not None:
        cat = cat.search(QueryTimeUntil(until))

    for k, v in keys.items():
        cat = cat.search(tiled.queries.Key(k) == v)

    for v in text:
        cat = cat.search(tiled.queries.FullText(v, case_sensitive=False))
    for v in text_case:
        cat = cat.search(tiled.queries.FullText(v, case_sensitive=True))
    return cat


def run_description_table(run):
    """Provide text description of the data streams."""
    import pyRestTable

    from . import analyze_run

    # Describe what will be plotted.
    analysis = analyze_run.SignalAxesFields(run).to_dict()
    table = pyRestTable.Table()
    table.labels = "item description".split()
    table.addRow(("scan", analysis["scan_id"]))
    table.addRow(("plan", analysis["plan"]))
    table.addRow(("chart", analysis["chart_type"]))
    if analysis["plot_signal"] is not None:
        table.addRow(("stream", analysis["stream"]))
        table.addRow(("plot signal", analysis["plot_signal"]))
        table.addRow(("plot axes", ", ".join(analysis["plot_axes"])))
        table.addRow(("all detectors", ", ".join(analysis["detectors"])))
        table.addRow(("all positioners", ", ".join(analysis["positioners"])))
    text = "plot summary"
    text += "\n" + "-" * len(text) + "\n" * 2
    text += f"{table.reST()}\n"

    # information about each stream
    rows = []
    for sname in run:
        title = f"stream: {sname}"
        rows.append(title)
        rows.append("-" * len(title))
        stream = run[sname]
        data = stream["data"].read()
        rows.append(str(data))
        rows.append("")

    text += "\n".join(rows).strip()
    return text


def run_summary(run):
    """Summary (text) of this run."""
    md = run.metadata
    return (
        f"{md.get('start', {}).get('plan_name', '')}"
        f" #{md.get('start', {}).get('scan_id', '?')}"
        # f" {utils.ts2iso(md.get('start', {}).get('time', 0))}"
        # f" ({md.get('start', {}).get('uid', '')[:7]})"
        f" {md.get('start', {}).get('title', '')}"
    ).strip()


def run_summary_table(runs):
    import pyRestTable

    table = pyRestTable.Table()
    table.labels = "# uid7 scan# plan #points exit started streams".split()
    for i, uid in enumerate(runs, start=1):
        run = runs[uid]
        md = run.metadata
        t0 = md["start"].get("time")
        table.addRow(
            (
                i,
                uid[:7],
                md["summary"].get("scan_id"),
                md["summary"].get("plan_name"),
                md["start"].get("num_points"),
                (md["stop"] or {}).get("exit_status"),  # if no stop document!
                datetime.datetime.fromtimestamp(t0).isoformat(sep=" "),
                ", ".join(md["summary"].get("stream_names")),
            )
        )
    return table


def stream_data_fields(stream):
    """
    Data field (names) of this BlueskyEventStream.

    Sort the list by relevance.

    First "time" (epoch timestamp for each event document), then "config" (the
    caller provided these names as parameters for this stream), then "data"
    (other signals in this stream, usually added from a Device hint).
    """
    # List any stream["config"] names first.
    fields = sorted(stream.get("config", []))

    # Other names from "data" are sorted alphabetically.
    for nm in sorted(stream.get("data", [])):
        if nm not in fields:
            fields.append(nm)

    # Promote "time" field to first place.
    if "time" in fields:
        fields.remove("time")
        fields.insert(0, "time")
    return fields


def stream_data_field_shape(stream, field_name):
    """Shape of this data field."""
    try:
        shape = stream["data"][field_name].shape
    except Exception:
        shape = ()
    return shape


def stream_data_field_pv(stream, field_name):
    """EPICS PV name of this field."""
    pv = ""
    try:
        descriptors = list(stream.metadata["descriptors"])
        assert len(descriptors) == 1, f"{stream=} has {len(descriptors)=}"
        source = descriptors[0]["data_keys"][field_name].get("source", "")
        if source.startswith("PV:"):
            pv = source[3:]
    except Exception:
        pass
    return pv


def stream_data_field_units(stream, field_name):
    """Engineering units of this field."""
    units = ""
    try:
        descriptors = list(stream.metadata["descriptors"])
        assert len(descriptors) == 1, f"{stream=} has {len(descriptors)=}"
        units = descriptors[0]["data_keys"][field_name].get("units", "")
    except Exception:
        pass
    return units
