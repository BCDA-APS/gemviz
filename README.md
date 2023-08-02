# tiled-viz2023

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

First said, this code is pre-release and may contain significant unhandled bugs.
Please [report any you encounter](https://github.com/BCDA-APS/gemviz/issues/new).

It is not yet installable as application now but you can run it as a developer would with these instructions:

1. Navigate to a directory where you have similar software projects
1. `git clone https://github.com/BCDA-APS/gemviz`
1. `cd gemviz`
1. `conda env create --force -n gemviz23 -f ./env.yml`
   - only need to do this once, assumes you have `conda` command
1. `conda activate gemviz23`
1. `cd gemviz23/demo`
1. `python app.py &`
