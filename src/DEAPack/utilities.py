
def dict_to_list(dict: dict) -> list:
    return [dict[k] for k in dict]


import pandas as pd
import importlib.resources
def load_example_data() -> pd.DataFrame:
    """
    Load example data for DEAPack Demo
    """
    file_path = importlib.resources.files('DEAPack').joinpath('data/example_data.csv')
    data = pd.read_csv(file_path)
    return data
