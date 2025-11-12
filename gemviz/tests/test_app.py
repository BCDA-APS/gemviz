"""Unit tests of the gemviz.app module."""

import sys

import pytest

from ..app import command_line_interface


@pytest.fixture
def argv():
    """Save & restore sys.argv for tests that change it."""
    old = sys.argv
    sys.argv = sys.argv[:1]
    yield sys.argv
    sys.argv = old


@pytest.mark.parametrize(
    "args, fragment",
    [
        [["-h"], "usage: pytest [-h]"],
        [["--help"], "usage: pytest [-h]"],
        [["-h"], "--log {critical,fatal,error,warn"],
        # Exact version string will change.
        # Delimiter is the only text available in any version.
        [["-v"], "."],
        [["--version"], "."],
    ],
)
def test_command_line_interface(args, fragment, argv, capsys):
    assert isinstance(argv, list)
    assert len(argv) == 1
    assert len(sys.argv) == 1

    sys.argv += args
    with pytest.raises(SystemExit) as exc:
        command_line_interface()
    assert exc.value.code == 0
    assert fragment in capsys.readouterr().out
