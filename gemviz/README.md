# notes

Terse summary of responsibilities of the source modules.

- app
  - parse command-line options
  - setup logging
  - starts GUI (MainWindow)
- MainWindow class
  - creates tiled client connection
  - passes client to BRC_MVC class
  - populate QComboBox with available catalog names
  - When catalog is selected from QComboBox, create BRC_MVC.
- BRC_MVC class
  - (re)created each time catalog is chosen:
    - set self.catalog
    - remove previous QTableView
    - create QTableView with default page offset and size
    - each time filters are changed or catalog is updated:
      - Set page offset from self.selected_uid (if not None)
      - update QTableView with fcat_md (page of filtered catalog metadata)
    - call SelectFieldsWidget when run is selected
    - call ChartView when requested by SelectFieldsWidget
  - BRCTableView class
    - page through a filtered CatalogOfBlueskyRuns
    - update BRCTableModel as page parameters or filtered catalog are changed
  - BRCTableModel class
    - display one page of runs in a table
    - select a run for examination
    - when run is selected, update self.selected_uid (emit a signal)
  - SelectFieldsWidget class
    - populate the table of plottable fields
    - identify default data to plot (if any) and check the boxes
    - request to plot data as directed by buttons
  - ChartView class
    - Determine dimensionality (and type of plot)
    - Only plots 1-D line charts now.
    - TODO: Expand to 2-D mesh and 2-D image views.

...
