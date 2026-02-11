from pathlib import Path
from typing import Union, Optional

import pandas as pd


def load_excel(
    path: Union[str, Path],
    sheet_name: Union[str, int] = 0,
    header: Optional[int] = 0,
) -> pd.DataFrame:
    """
    Load data from an Excel file into a pandas DataFrame.

    Parameters
    ----------
    path : str or Path
        Path to the Excel file.
    sheet_name : str or int, default 0
        Sheet name or index to read.
    header : int or None, default 0
        Row number to use as column names (0-based).
    """

    return pd.read_excel(
        path,
        sheet_name=sheet_name,
        header=header,
    )