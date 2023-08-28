# gemviz

Python Qt5 application to visualize Bluesky data from tiled server.

## Goals

- minimum: PyQt app that can select runs, show line charts
- ideal: add database filters, config file, autodetect data types, and representations
- stretch: data visualization integrate with https://github.com/BCDA-APS/qs-web2023

## Web Links

- https://github.com/bluesky/tiled
- https://github.com/bluesky/bluesky-widgets
- [Tiled Python Client Demonstration](https://github.com/BCDA-APS/bdp-tiled/blob/main/demo_client.ipynb) - shows the JSON API between tiled server and client
- [Tiled Python Client Python API](https://github.com/BCDA-APS/bdp-tiled/blob/main/pyapi_client.py) - terse example using `tiled.client` libary

## How to run this code?

First said, this software application is pre-release and may contain significant unhandled
bugs.  Please [report any you encounter](https://github.com/BCDA-APS/gemviz/issues/new) or
feature requests, too.

Suggested installation for developers is to use
`pip` with its *editable* mode:

This project is still in development.
We have [plans for production
release](https://github.com/orgs/BCDA-APS/projects/6).
Until the production release, you should run `gemviz`
as would a developer by following these instructions:

1. Navigate to a directory where you have similar software projects
2. `git clone https://github.com/BCDA-APS/gemviz`
   - only need to do this once, assumes you have `git` command
3. `cd gemviz`
4. `conda env create --force -n gemviz -f ./env.yml`
   - only need to do this once, assumes you have `conda` command
5. `conda activate gemviz`
6. `pip install -e .`
7. `gemviz &`

## Acknowledgements

We'd like to thank the [GEM fellow program](https://www.gemfellowship.org/) for sponsoring
an intern fellowship for the development of this software at the Advanced Photon Source.

"This product includes software produced by UChicago Argonne, LLC 
under Contract No. DE-AC02-06CH11357 with the Department of Energy."
