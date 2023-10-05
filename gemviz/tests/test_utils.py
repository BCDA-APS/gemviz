import datetime

import pytest
from PyQt5 import QtWidgets

from .. import utils

# TODO: run_in_thread


# FIXME:  problems here with the time zone
#   2024-02-04T13:14:15Z not recognized some times
# @pytest.mark.parametrize(
#     "iso, ts",
#     [  # test using America/Chicago time zone
#         ["2024-02-04T13:14:15", 1_707_052_455],  # 1_707_074_055
#         ["1990-01-01", 631_152_000],  # 631_173_600
#         ["1969-12-31T18:00", -21_600],  # 0
#     ],
# )
# def test_iso2ts(iso, ts):
#     assert isinstance(iso, str)
#     assert isinstance(ts, (int, float))
#     assert utils.iso2ts(iso) == ts


@pytest.mark.parametrize(
    "iso, dt",
    [
        ["2024-04-01T13:14:15", datetime.datetime(2024, 4, 1, 13, 14, 15)],
        ["1990-01-01", datetime.datetime(1990, 1, 1)],
        ["1970-01-01", datetime.datetime(1970, 1, 1)],
    ],
)
def test_iso2dt(iso, dt):
    assert isinstance(iso, str)
    assert isinstance(dt, datetime.datetime)
    assert utils.iso2dt(iso) == dt


@pytest.mark.parametrize(
    "ts, dt",
    [
        # fmt: off
        [0, datetime.datetime(1970, 1, 1)],
        [1_707_052_455, datetime.datetime(2024, 2, 4, 13, 14, 15)],
        [631_152_000, datetime.datetime(1990, 1, 1)],
        # fmt: on
    ],
)
def test_ts2dt(ts, dt):
    # complication here is that dt has the local timezone
    ts_offset = datetime.datetime(1970, 1, 1).timestamp()
    assert utils.ts2dt(ts + ts_offset) == dt


@pytest.mark.parametrize(
    "ts, iso",
    [
        [0, "1970-01-01 00:00:00"],
        [1_707_052_455, "2024-02-04 13:14:15"],
        [631_152_000, "1990-01-01 00:00:00"],
    ],
)
def test_ts2iso(ts, iso):
    # complication here is that dt has the local timezone
    ts_offset = datetime.datetime(1970, 1, 1).timestamp()
    assert utils.ts2iso(ts + ts_offset) == iso


@pytest.mark.parametrize(
    "fname, uiname",
    [
        ["simple.py", "simple.ui"],
        ["simple.extension_ignored", "simple.ui"],
        ["simple.ui", "simple.ui"],
        ["path/ignored/simple.py", "simple.ui"],
    ],
)
def test_getUiFileName(fname, uiname):
    assert utils.getUiFileName(fname) == uiname


@pytest.mark.parametrize(
    "uiname, parts",
    [
        ["bluesky_runs_catalog.ui", "hsplitter vsplitter".split()],
        ["date_time_range_slider.ui", "apply slider high_date".split()],
        ["select_stream_fields.ui", "streams run_summary groupbox".split()],
    ],
)
def test_myLoadUi(uiname, parts, qtbot):
    class Widget(QtWidgets.QWidget):
        ui_file = utils.getUiFileName(uiname)

        def __init__(self, parent):
            self.parent = parent
            super().__init__()
            utils.myLoadUi(self.ui_file, baseinstance=self)

    widget = Widget(None)
    qtbot.addWidget(widget)
    widget.show()

    for p in parts:
        assert hasattr(widget, p)


@pytest.mark.parametrize(
    "uiname, groupbox",
    [
        ["bluesky_runs_catalog.ui", "fields_groupbox"],
        ["bluesky_runs_catalog.ui", "filter_groupbox"],
        ["bluesky_runs_catalog.ui", "runs_groupbox"],
        ["bluesky_runs_catalog.ui", "viz_groupbox"],
    ],
)
def test_removeAllLayoutWidgets(uiname, groupbox, qtbot):
    class Widget(QtWidgets.QWidget):
        ui_file = utils.getUiFileName(uiname)

        def __init__(self, parent):
            self.parent = parent
            super().__init__()
            utils.myLoadUi(self.ui_file, baseinstance=self)

    widget = Widget(None)
    qtbot.addWidget(widget)
    widget.show()

    layout = getattr(widget, groupbox).layout()
    assert isinstance(layout, QtWidgets.QLayout)
    assert len(layout) == 0

    layout.addWidget(QtWidgets.QWidget(None))
    assert len(layout) == 1

    utils.removeAllLayoutWidgets(layout)
    assert len(layout) == 0
