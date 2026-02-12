from pathlib import Path
from typing import Union

import pandas as pd


def load_csv(path: Union[str, Path]) -> pd.DataFrame:

    df = pd.read_csv(path)

    # Standardize column names
    df.columns = df.columns.str.strip().str.lower()

    return df