====================================
Installation Guide
====================================

First said, this software application is pre-release and may contain significant
unhandled bugs.  Please report any issues you encounter
(https://github.com/BCDA-APS/gemviz/issues/new) or feature requests, too.

Suggested installation for developers is to use
``pip`` with its *editable* mode:

This project is still in development. We have plans for production release
(https://github.com/orgs/BCDA-APS/projects/6). Until the production release, you
should run ``gemviz`` as would a developer by following these (Linux) instructions:

1. Navigate to a directory where you have similar software projects
2. ``git clone https://github.com/BCDA-APS/gemviz``
   - only need to do this once, assumes you have ``git`` command
3. ``cd gemviz``
4. ``conda env create --force -n gemviz -f ./env.yml``
   - only need to do this once, assumes you have ``conda`` command
5. ``conda activate gemviz``
6. ``pip install -e .``
7. ``gemviz &``

