import pytest

import gemviz  # TODO: Can this become a relative import?


def getvar(var_name):
    assert var_name in dir(gemviz)
    return getattr(gemviz, var_name)


def apply_str_assertion(var, where, fragment):
    if where == "start":
        assert var.startswith(fragment)
    elif where == "end":
        assert var.endswith(fragment)
    elif where == "contains":
        assert fragment in var
    elif where == "equals":
        assert var == fragment


@pytest.mark.parametrize(
    "var_name, where, fragment",
    [
        ["__package_name__", "equals", "gemviz"],
        ["__settings_orgName__", "equals", "BCDA-APS"],
        ["__version__", "contains", "."],
        ["APP_DESC", "equals", "Visualize Bluesky data from tiled server."],
        ["APP_TITLE", "equals", "gemviz"],
        ["AUTHOR_LIST", "contains", "Fanny Rodolakis"],
        ["AUTHOR_LIST", "contains", "Ollivier Gassant"],
        ["AUTHOR_LIST", "contains", "Pete Jemian"],
        ["COPYRIGHT_TEXT", "contains", "see LICENSE file"],
        ["COPYRIGHT_TEXT", "contains", "UChicago Argonne, LLC"],
        ["COPYRIGHT_TEXT", "start", "(c)"],
        ["DOCS_URL", "contains", "BCDA-APS/gemviz"],
        ["DOCS_URL", "start", "https://"],
        ["ISSUES_URL", "contains", "BCDA-APS/gemviz"],
        ["ISSUES_URL", "end", "issues"],
        ["ISSUES_URL", "start", "https://"],
    ],
)
def test_text_content(var_name, where, fragment):
    apply_str_assertion(getvar(var_name), where, fragment)


@pytest.mark.parametrize(
    "var_name, where, fragment",
    [
        ["LICENSE_FILE", "end", "LICENSE"],
        ["UI_DIR", "end", "resources"],
    ],
)
def test_paths(var_name, where, fragment):
    apply_str_assertion(str(getvar(var_name)), where, fragment)


def test_license_file():
    """Is the license file present?"""
    assert gemviz.LICENSE_FILE.exists()
