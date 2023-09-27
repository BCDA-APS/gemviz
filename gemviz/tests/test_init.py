import pathlib

import pytest

from ..__init__ import APP_DESC
from ..__init__ import APP_TITLE
from ..__init__ import AUTHOR_LIST
from ..__init__ import COPYRIGHT_TEXT
from ..__init__ import DOCS_URL
from ..__init__ import ISSUES_URL
from ..__init__ import LICENSE_FILE
from ..__init__ import UI_DIR
from ..__init__ import __package_name__
from ..__init__ import __settings_orgName__
from ..__init__ import __version__


def apply_str_assertion(var, where, fragment):
    assert isinstance(var, str)
    if where == "start":
        assert var.startswith(fragment)
    elif where == "end":
        assert var.endswith(fragment)
    elif where == "contains":
        assert fragment in var
    elif where == "equals":
        assert var == fragment


@pytest.mark.parametrize(
    "var, where, fragment, type_",
    [
        [__package_name__, "equals", "gemviz", str],
        [__settings_orgName__, "equals", "BCDA-APS", str],
        [__version__, "contains", ".", str],
        [APP_DESC, "equals", "Visualize Bluesky data from tiled server.", str],
        [APP_TITLE, "equals", "gemviz", str],
        [AUTHOR_LIST, "contains", "Fanny Rodolakis", list],
        [AUTHOR_LIST, "contains", "Ollivier Gassant", list],
        [AUTHOR_LIST, "contains", "Pete Jemian", list],
        [COPYRIGHT_TEXT, "contains", "see LICENSE file", str],
        [COPYRIGHT_TEXT, "contains", "UChicago Argonne, LLC", str],
        [COPYRIGHT_TEXT, "start", "(c)", str],
        [DOCS_URL, "contains", "BCDA-APS/gemviz", str],
        [DOCS_URL, "start", "https://", str],
        [ISSUES_URL, "contains", "BCDA-APS/gemviz", str],
        [ISSUES_URL, "end", "issues", str],
        [ISSUES_URL, "start", "https://", str],
        [LICENSE_FILE, "end", "LICENSE", pathlib.Path],
        [UI_DIR, "end", "resources", pathlib.Path],
    ],
)
def test_text_content(var, where, fragment, type_):
    assert isinstance(var, type_)
    apply_str_assertion(str(var), where, fragment)


def test_license_file():
    """Is the license file present?"""
    assert LICENSE_FILE.exists()
