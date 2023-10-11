import numpy as np
import pytest

from .. import chartview


@pytest.mark.parametrize(
    "quantity, series, auto",
    [
        [16, chartview.PLOT_COLORS, chartview.auto_color],
        [9, chartview.PLOT_SYMBOLS, chartview.auto_symbol],
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
@pytest.mark.parametrize("x", [None, "axis label"])
@pytest.mark.parametrize("y", [None, "axis label"])
def test_ChartView_labels(title, x, y, qtbot):
    chart = chartview.ChartView(None)
    assert chart.parent is None

    qtbot.addWidget(chart)
    chart.show()

    pw = chart.plot_widget
    assert pw.plotItem.titleLabel.text == ""
    assert pw.getAxis("bottom").label.toPlainText() in ("", "(None)")
    assert pw.getAxis("left").label.toPlainText() in ("", "(None)")

    if title is not None:
        chart.setPlotTitle(title)
        assert pw.plotItem.titleLabel.text == title

    if x is not None:
        chart.setBottomAxisText(x)
        assert pw.getAxis("bottom").label.toPlainText().strip() == x

    if y is not None:
        chart.setLeftAxisText(y)
        assert pw.getAxis("left").label.toPlainText().strip() == y


# TODO: test with timestamps
# fmt: off
@pytest.mark.parametrize("x", [np.array([1, 2, 3, 4, 5]), None])
@pytest.mark.parametrize(
    "y", [np.array([1, 2, 3, 4, 5]), np.array([2, 2, 2, 2, 2])]
)
# fmt: on
def test_ChartView_data(x, y, qtbot):
    chart = chartview.ChartView(None)
    if x is None:
        chart.plot(y)
    else:
        chart.plot(x, y)
    qtbot.addWidget(chart)
    chart.show()

    # Test for the plot data.
    pw = chart.plot_widget
    curves = pw.getPlotItem().curves

    if len(curves) > 0:
        curve = curves[0].curve
        assert curve.yData.shape == y.shape  # compare shapes
        assert (curve.yData == y).all()  # compare values
        if x is None:
            assert curve.xData.shape == y.shape
            assert (curve.xData != x).all()
        else:
            assert curve.xData.shape == x.shape
            assert (curve.xData == x).all()
