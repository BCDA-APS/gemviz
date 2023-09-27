Developer - Testing the Code
============================

Running the tests
-----------------

Following `advice from
pytest <https://docs.pytest.org/en/7.1.x/explanation/goodpractices.html>`__:

.. code:: bash

   pytest -vvv --lf --pyargs gemviz

Installing Packages for Unit Testing
------------------------------------

Need to add some packages to run the tests:

.. code:: bash

   conda install pytest pytest-qt pytest-cov -c conda-forge -c defaults

or

.. code:: bash

   pip install -r ./requirements-dev.txt
