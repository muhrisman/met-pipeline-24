import pandas as pd
from pathlib import Path


def load_excel(path: str | Path, sheet_name: str | int = 0) -> pd.DataFrame:
    """
    Load data from an Excel file into a pandas DataFrame.

    This function is intended for development and validation workflows.
    The returned DataFrame can be passed directly to analysis functions.
    """
    return pd.read_excel(path, sheet_name=sheet_name)