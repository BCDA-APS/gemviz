"""
Local support for the tiled API & data structures.

.. autosummary:

    ~run_summary
    ~stream_data_fields
    ~stream_data_field_shape
"""

from . import utils


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
