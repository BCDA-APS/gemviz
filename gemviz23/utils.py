"""
Support functions for this demo project.
"""

import datetime

import tiled.queries


def iso2time(isotime):
    return datetime.datetime.timestamp(datetime.datetime.fromisoformat(isotime))


def QueryTimeSince(isotime):
    return tiled.queries.Key("time") >= iso2time(isotime)


def QueryTimeUntil(isotime):
    return tiled.queries.Key("time") < iso2time(isotime)


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
                (md["stop"] or {}).get("exit_status"),  # rare case of no stop document!
                datetime.datetime.fromtimestamp(t0).isoformat(sep=" "),
                ", ".join(md["summary"].get("stream_names")),
            )
        )
    return table


def main():
    from tiled.client import from_uri
    from tiled.client.cache import Cache
    from tiled.utils import tree

    tiled_server = "otz.xray.aps.anl.gov"
    tiled_server_port = 8000
    catalog = "developer"
    start_time = "2021-03-17 00:30"
    end_time = "2021-05-19 15:15"

    # connect our client with the server
    uri = f"http://{tiled_server}:{tiled_server_port}"
    print(f"{uri=}")
    client = from_uri(uri, cache=Cache.in_memory(2e9))
    print(f"{client=}")
    print(f"{catalog=}")
    cat = client[catalog]
    print(f"{cat=}")
    print(run_summary_table(cat))

    cat = get_tiled_runs(cat, since=start_time, until=end_time, plan_name="rel_scan")
    print(f"filtered: {cat=}")
    print(run_summary_table(cat))

    text = "noisy"
    cat = get_tiled_runs(cat, text=[text])
    print(f"filtered runs with {text!r} as text: {cat=}")
    print(run_summary_table(cat))

    text = "save & restore"
    # text = "locate_image_peak"
    # text = "tscan"
    # text = "gp:scaler1"
    # text = "zaxis"
    cat = get_tiled_runs(
        client[catalog],
        text=[text],
        # pid=154446
    )
    print(f"all runs with {text!r} as text: {cat=}")
    print(run_summary_table(cat))


if __name__ == "__main__":
    main()
