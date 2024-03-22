import numpy as np
import pytest

from .. import chartview


@pytest.mark.parametrize(
    "quantity, series, auto",
    [
        [17, chartview.PLOT_COLORS, chartview.auto_color],
        [8, chartview.PLOT_SYMBOLS, chartview.auto_symbol],
    ],
)
def test_auto_series(quantity, series, auto):
    n = len(series)
    assert n == quantity

    # Test that one pass of the sequence generates unique values.
    series = [auto() for _ in range(n)]
    assert len(set(series)) == n

    # Test that series repeats exactly.
    series2 = [auto() for _ in range(n)]
    assert series == series2


@pytest.mark.parametrize("title", [None, "one line text"])
@pytest.mark.parametrize("subtitle", [None, "the subtitle"])
@pytest.mark.parametrize("x", [None, "axis label"])
@pytest.mark.parametrize("y", [None, "axis label"])
def test_ChartView_annotations(title, subtitle, x, y, qtbot):
    chart = chartview.ChartView(None)
    assert chart.parent is None

    qtbot.addWidget(chart)
    chart.show()

    fig = chart.figure
    ax = chart.main_axes

    try:
        # new method in MPL 3.8
        assert fig.get_suptitle() in ("", "(None)"), f"{dir(fig)}"
        has_get_suptitle = True
    except AttributeError:
        # not in MPL 3.7.3
        has_get_suptitle = False
    assert ax.get_title() in ("", "(None)")
    assert ax.get_xlabel() in ("", "(None)")
    assert ax.get_ylabel() in ("", "(None)")

    if title is not None and has_get_suptitle:
        chart.setPlotTitle(title)
        assert fig.get_suptitle() == title

    if subtitle is not None:
        chart.setPlotSubtitle(subtitle)
        assert ax.get_title() == subtitle

    if x is not None:
        chart.setBottomAxisText(x)
        assert ax.get_xlabel().strip() == x

    if y is not None:
        chart.setLeftAxisText(y)
        assert ax.get_ylabel().strip() == y


# TODO: test with timestamps
# fmt: off
@pytest.mark.parametrize("x", [np.array([1, 2, 3, 4, 5]), None])
@pytest.mark.parametrize(
    "y", [np.array([1, 2, 3, 4, 5]), np.array([2, 2, 2, 2, 2])]
)
# fmt: on
def test_ChartView_data(x, y, qtbot):
    chart = chartview.ChartView(None)
    label = "testing"
    if x is None:
        chart.plot(y, label=label)
    else:
        chart.plot(x, y, label=label)
    qtbot.addWidget(chart)
    chart.show()

    # Test for the plot data.
    if len(chart.curves) > 0:
        data = chart.curves[label]
        if x is None:
            assert len(data) == 2
            line2d, yraw = data
            # With only y data, Line2D fills x with index number, starting at 0.
            assert len(line2d.get_data()) == 2
            xarr, yarr = line2d.get_data()
            assert isinstance(yarr, type(yraw))
            assert len(yarr) == len(yraw)
            assert xarr[-1] == len(yraw) - 1
        else:
            assert len(data) == 3
            line2d, xraw, yraw = data
            assert xraw.shape == yraw.shape
            assert len(line2d.get_data()) == 2
            xarr, yarr = line2d.get_data()
            assert isinstance(xarr, type(xraw))
            assert isinstance(yarr, type(yraw))
            assert len(xarr) == len(xraw)
            assert len(yarr) == len(yraw)
