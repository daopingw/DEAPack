# DEAPack: A Data Envelopment Analysis Package

DEAPack is a Python package designed for Data Envelopment Analysis (DEA). Its comprehensive toolset allows for efficient handling of various DEA models, including those that account for undesirable outputs.

## Installation

Install the package by `pip`,

```sh
pip install DEAPack
```
Or install the package by `conda`,
```sh
conda install DEAPack
```

## Usage

A brief example is provided below. For more information, please refer to the [documentation]() and [example notebooks]().

```python
# import the module
from DEAPack.model import DEA
from DEAPack.utilities import load_example_data

# load the example dataset
data = load_example_data()

# initilise a DEA model
model = DEA()

# specify the DEA model
model.DMUs = data['region']
model.time = data['year']
model.x_vars = data[['K', 'L', 'E']]
model.y_vars = data[['Y']]
model.b_vars = data[['CO2']]

# solve the DEA model
model.solve()

# get estimated efficiencies
results = model.get_efficiency()
```

## Communication

You're very welcome to contribute to this package. We appreciate any efforts to improve this package. You can help by adding new features, reporting bugs, or extending the documentation and usage examples. Please contact us if you have any ideas.

- [Pull requests](https://github.com/daopingw/DEAPack/pulls) for pull requests.
- [Issues](https://github.com/daopingw/DEAPack/issues) for bug reports.
