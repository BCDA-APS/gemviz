"""
Define constants used throught the code.
"""

import pathlib

try:
    from setuptools_scm import get_version

    __version__ = get_version(root="..", relative_to=__file__)
    del get_version
except (LookupError, ModuleNotFoundError):
    from importlib.metadata import version

    __version__ = version("pkgdemo")
    del version

__settings_orgName__ = "BCDA-APS"
__package_name__ = "gemviz"

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

COPYRIGHT_TEXT = "(c) 2023, UChicago Argonne, LLC, (see LICENSE file for details)"
DOCS_URL = "https://github.com/BCDA-APS/tiled-viz2023/blob/main/README.md"
ISSUES_URL = "https://github.com/BCDA-APS/tiled-viz2023/issues"
LICENSE_FILE = ROOT_DIR / "LICENSE"
VERSION = "0.0.1"
