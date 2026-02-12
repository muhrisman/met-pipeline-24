from pathlib import Path
from typing import Union, Optional

import pandas as pd


def load_excel(
    path: Union[str, Path],
    sheet_name: Union[str, int] = 0,
    header: Optional[int] = 0,
) -> pd.DataFrame:

    df = pd.read_excel(
        path,
        sheet_name=sheet_name,
        header=header,
    )

    # Standardize column names
    df.columns = df.columns.str.strip().str.lower()

    return df