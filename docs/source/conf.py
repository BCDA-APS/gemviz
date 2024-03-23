# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

import pathlib
import sys
import tomllib
from importlib.metadata import version

sys.path.insert(0, str(pathlib.Path().absolute().parent.parent))
import gemviz  # noqa

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

root_path = pathlib.Path(__file__).parent.parent.parent

with open(root_path / "pyproject.toml", "rb") as fp:
    toml = tomllib.load(fp)
metadata = toml["project"]

gh_org = "BCDA-APS"
project = metadata["name"]
copyright = toml["tool"]["copyright"]["copyright"]
author = "Ollivier Gassant, Fanny Rodolakis, Pete Jemian"
description = metadata["description"]
rst_prolog = f".. |author| replace:: {author}"
github_url = f"https://github.com/{gh_org}/{project}"

# -- Special handling for version numbers ------------------------------------
# https://github.com/pypa/setuptools_scm#usage-from-sphinx

release = version(project)
version = ".".join(release.split(".")[:2])

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = """
    sphinx.ext.autodoc
    sphinx.ext.autosummary
    sphinx.ext.coverage
    sphinx.ext.githubpages
    sphinx.ext.inheritance_diagram
    sphinx.ext.mathjax
    sphinx.ext.todo
    sphinx.ext.viewcode
""".split()

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]

autodoc_mock_imports = """
    h5py
    matplotlib
    numpy
    pyqt5
    pyRestTable
    spec2nexus
    tiled
    xarray
""".split()
