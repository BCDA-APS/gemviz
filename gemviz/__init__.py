"""
Define constants used throught the code.
"""

import pathlib

__settings_orgName__ = "BCDA-APS"
__package_name__ = "gemviz"

try:
    from setuptools_scm import get_version

    __version__ = get_version(root="..", relative_to=__file__)
    del get_version
except (LookupError, ModuleNotFoundError):
    from importlib.metadata import version

    __version__ = version(__package_name__)
    del version

ROOT_DIR = pathlib.Path(__file__).parent
UI_DIR = ROOT_DIR / "resources"

APP_DESC = "Visualize Bluesky data from tiled server."
APP_TITLE = __package_name__
AUTHOR_LIST = [
    s.strip()
    for s in """
        Ollivier Gassant
        Fanny Rodolakis
        Pete Jemian
    """.strip().splitlines()
]

# fmt: off
COPYRIGHT_TEXT = (
    "(c) 2023, UChicago Argonne, LLC"
    ", (see LICENSE file for details)"
)
# fmt: on
DOCS_URL = "https://github.com/BCDA-APS/gemviz/blob/main/README.md"
ISSUES_URL = "https://github.com/BCDA-APS/gemviz/issues"
LICENSE_FILE = ROOT_DIR / "LICENSE"
