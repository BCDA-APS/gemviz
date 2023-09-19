# Start unit tests

## Installing Packages

Need to add some packages to run the tests:

```bash
conda install pytest pytest-qt pytest-cov -c conda-forge -c defaults
```

## Running the tests

Following [advice from
pytest](https://docs.pytest.org/en/7.1.x/explanation/goodpractices.html):

```bash
pytest -vvv --lf --pyargs gemviz
```
