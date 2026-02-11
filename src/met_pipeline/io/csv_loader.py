from pathlib import Path
from typing import Union

import pandas as pd


def load_csv(path: Union[str, Path]) -> pd.DataFrame:
    """
    Load data from a CSV file into a pandas DataFrame.
    """
    return pd.read_csv(path)