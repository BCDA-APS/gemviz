"""
Support functions for this demo project.
"""

import datetime
import pathlib

import tiled.queries

ROOT_DIR = pathlib.Path(__file__).parent

APP_DESC = "Visualize Bluesky data from tiled server."
APP_TITLE = "GemViz23"
AUTHOR_LIST = """
    Ollivier Gassant
    Fanny Rodolakis
    Pete Jemian
""".strip().splitlines()
COPYRIGHT_TEXT = "(c) 2023, UChicago Argonne, LLC, (see LICENSE file for details)"
DOCS_URL = "https://github.com/BCDA-APS/tiled-viz2023/blob/main/README.md"
ISSUES_URL = "https://github.com/BCDA-APS/tiled-viz2023/issues"
LICENSE_FILE = ROOT_DIR / "LICENSE"
UI_DIR = ROOT_DIR / "resources"
VERSION = "0.0.1"


def iso2time(isotime):
    dt = datetime.datetime.fromisoformat(isotime)
    return datetime.datetime.timestamp(dt)


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
                (md["stop"] or {}).get("exit_status"),  # if no stop document!
                datetime.datetime.fromtimestamp(t0).isoformat(sep=" "),
                ", ".join(md["summary"].get("stream_names")),
            )
        )
    return table


def myLoadUi(ui_file, baseinstance=None, **kw):
    """
    Load a .ui file for use in building a GUI.

    Wraps `uic.loadUi()` with code that finds our program's
    *resources* directory.

    :see: http://nullege.com/codes/search/PyQt4.uic.loadUi
    :see: http://bitesofcode.blogspot.ca/2011/10/comparison-of-loading-techniques.html

    inspired by:
    http://stackoverflow.com/questions/14892713/how-do-you-load-ui-files-onto-python-classes-with-pyside?lq=1
    """
    from PyQt5 import uic

    if isinstance(ui_file, str):
        ui_file = UI_DIR / ui_file

    return uic.loadUi(ui_file, baseinstance=baseinstance, **kw)
