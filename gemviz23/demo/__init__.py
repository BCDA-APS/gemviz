"""
Define constants used throught the code.
"""

import pathlib

__settings_orgName__ = "BCDA-APS"
__package_name__ = "gemviz23"

ROOT_DIR = pathlib.Path(__file__).parent
UI_DIR = ROOT_DIR / "resources"

APP_DESC = "Visualize Bluesky data from tiled server."
APP_TITLE = "GemViz23"
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
