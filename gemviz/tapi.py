"""
TAPI: Local support for the tiled API & data structures.

.. autosummary:

    ~connect_tiled_server
    ~get_tiled_runs
    ~QueryTimeSince
    ~QueryTimeUntil
    ~RunMetadata
    ~TiledServerError
"""

import logging

import tiled
import tiled.queries
from httpx import HTTPStatusError

logger = logging.getLogger(__name__)


class TiledServerError(RuntimeError):
    """An error from the tiled server."""


class RunMetadata:
    """Cache the metadata for a single run."""

    def __init__(self, cat, uid):
        self.catalog = cat
        self.uid = uid
        self.request_from_tiled_server()

    def __str__(self) -> str:
        return (
            f"{__class__.__name__}(catalog={self.catalog.item['id']!r},"
            f" uid7={self.uid[:7]!r},"
            f" active={self.active})"
        )

    def request_from_tiled_server(self):
        """Get run details from server."""
        self.run = self.catalog[self.uid]
        self.run_md = self.run.metadata
        self.active = (
            self.uid == self.catalog.keys().last() and "stop" not in self.run_md
        )
        self.streams_md = None
        self.streams_data = None

    def get_run_md(self, doc, key, default=None):
        """Get metadata by key from run document."""
        return (self.run_md.get(doc) or {}).get(key, default)

    def plottable_signals(self):
        """
        Return a dict with the plottable data for this run.

        * field: any available numeric data keys
        * motors: any data keys for motors declared by the run
        * detectors: any numeric data keys that are not motors or excluded names
        * plot_signal: the first detector signal
        * plot_axes: the first motor signal for each dimension

        * run.metadata[hints][dimensions] show the independent axes object names
        * Any given dimension may have more than one motor object (a2scan, ...)
        * This code chooses to only use the first motor of each dimension.
        * The stream descriptor list is usually length = 1.
        * object_keys are used to get lists of data_keys (fields)
        """

        def find_name_device_or_signal(key):
            if key in stream_hints:  # from ophyd.Device
                return stream_hints[key]["fields"]
            elif key in descriptor["data_keys"]:  # from ophyd.Signal
                return [key]
            raise KeyError(f"Could not find {key=}")

        def get_signal(key):
            try:
                return find_name_device_or_signal(key)[0]  # just the first one
            except KeyError:
                if key != "time":
                    raise KeyError(f"Unexpected key: {key!r}")
                return key  # "time" is a special case

        def is_numeric(signal):
            dtype = descriptor["data_keys"][signal]["dtype"]
            if dtype == "array":
                stream_data = self.stream_data(self.stream_name)
                ntype = stream_data["data"][signal].dtype.name
                if ntype.startswith("int") or ntype.startswith("float"):
                    dtype = "number"
            return dtype == "number"

        # dimensions of the run
        run_dims = self.get_run_md("start", "hints", {}).get("dimensions", [])

        # data stream to be used
        streams = [d[1] for d in run_dims]
        if len(set(streams)) != 1:
            # All hinted dimensions should come from the same stream.
            raise ValueError(f"Not handling hinted dimensions: {run_dims=}")
        stream = streams[0]

        # description of the data stream objects
        descriptors = self.stream_metadata(stream).get("descriptors", {})
        if len(descriptors) != 1:
            raise ValueError(f"Not handling situation of {len(descriptors)=}")

        descriptor = descriptors[0]

        # Mapping from object_keys to data_keys.
        stream_hints = descriptor.get("hints", {})

        # First motor signal for each dimension.
        try:
            axes = [get_signal(d[0][0]) for d in run_dims]
        except KeyError as exc:
            raise exc

        # All motor signals.
        motors = [
            signal
            for motor in self.get_run_md("start", "motors", [])
            for signal in find_name_device_or_signal(motor)
        ]

        # All detector signals.
        detectors = [
            signal
            for detector in self.get_run_md("start", "detectors")
            for signal in find_name_device_or_signal(detector)
            if is_numeric(signal)
        ]

        fields = []
        for descriptor in descriptors:
            hints = descriptor.get("hints", {})
            for obj_name in descriptor["object_keys"]:
                try:
                    signals = hints.get(obj_name, {})["fields"]
                except KeyError:
                    # ``ophyd.Device`` can have multiple signals
                    signals = descriptor["object_keys"].get(obj_name, [])
                fields.extend([k for k in signals if is_numeric(k)])

        status = self.get_run_md("stop", "exit_status")
        plot_signal = None
        if status in "abort success".split():
            # These runs probably have plottable data fields.

            # Do not choose any of these fields as the default
            # (NeXus-style plottable) signal data.
            not_plottable_signals = """
                timebase
                preset_time
            """.split()

            names_to_avoid = motors + not_plottable_signals
            possible_signals = detectors + fields
            for field in possible_signals:
                if field not in names_to_avoid:
                    plot_signal = field
                    break

        return {
            "catalog": self.catalog.item["id"],
            "uid": self.uid,
            "stream": stream,
            "plot_signal": plot_signal,
            "plot_axes": axes,
            "motors": motors,
            "detectors": detectors,
            "fields": fields,
        }

    def stream_data(self, stream_name):
        """Return the data structure for this stream."""
        if self.streams_data is None:
            # Optimize with a cache.
            self.streams_data = {
                sname: self.run[sname]["data"].read() for sname in self.run
            }

        return self.streams_data[stream_name]

    def stream_data_field_shape(self, stream_name, field_name):
        """Shape of this data field."""
        stream = self.stream_data(stream_name)
        try:
            shape = stream[field_name].shape
        except Exception:
            shape = ()
        return shape

    def stream_data_fields(self, stream_name):
        """
        Data field (names) of this BlueskyEventStream.

        Sort the list by relevance.

        First "time" (epoch timestamp for each event document), then "config" (the
        caller provided these names as parameters for this stream), then "data"
        (other signals in this stream, usually added from a Device hint).
        """
        fields = sorted(self.stream_data(stream_name))

        # Promote "time" field to first place.
        if "time" in fields:
            fields.remove("time")
        fields.insert(0, "time")
        return fields

    def stream_data_field_pv(self, stream_name, field_name):
        """EPICS PV name of this field."""
        pv = ""
        try:
            descriptors = self.stream_metadata(stream_name).get("descriptors", {})
            assert len(descriptors) == 1, f"{stream_name=} has {len(descriptors)=}"
            source = descriptors[0]["data_keys"][field_name].get("source", "")
            if source.startswith("PV:"):
                pv = source[3:]
        except Exception:
            pass
        return pv

    def stream_data_field_units(self, stream_name, field_name):
        """Engineering units of this field."""
        units = ""
        try:
            descriptors = self.stream_metadata(stream_name).get("descriptors", {})
            assert len(descriptors) == 1, f"{stream_name=} has {len(descriptors)=}"
            units = descriptors[0]["data_keys"][field_name].get("units", "")
        except Exception:
            pass
        return units

    def stream_metadata(self, stream_name=None):
        """Return the metadata dictionary for this stream."""
        if self.streams_md is None:
            # Optimize with a cache.
            self.streams_md = {sname: self.run[sname].metadata for sname in self.run}

        if stream_name is None:
            return self.streams_md
        return self.streams_md[stream_name]

    def summary(self):
        """Summary (text) of this run."""
        return (
            f"{self.get_run_md('start', 'scan_id', '?')}"
            f" {self.get_run_md('start', 'plan_name', '')}"
            f" {self.get_run_md('start', 'title', '')}"
        ).strip()


def connect_tiled_server(uri):
    """Make connection with the tiled server URI.  Return a client object."""
    from tiled.client import from_uri

    # leave out "dask" and get numpy by default
    # https://examples.dask.org/array.html
    # > Call .compute() when you want your result as a NumPy array.
    client = from_uri(uri, "dask")
    return client


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
    from . import utils

    return tiled.queries.Key("time") >= utils.iso2ts(isotime)


def QueryTimeUntil(isotime):
    """Tiled client query: all runs until given date/time."""
    from . import utils

    return tiled.queries.Key("time") <= utils.iso2ts(isotime)


def get_run(uri=None, catalog="training", reference=None):
    """Get referenced run from tiled server catalog."""
    # from gemviz.tapi import connect_tiled_server
    # from gemviz.tapi import get_tiled_runs

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


# -----------------------------------------------------------------------------
# :copyright: (c) 2023-2024, UChicago Argonne, LLC
#
# Distributed under the terms of the Argonne National Laboratory Open Source License.
#
# The full license is in the file LICENSE.txt, distributed with this software.
# -----------------------------------------------------------------------------
