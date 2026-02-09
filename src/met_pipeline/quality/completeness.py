import pandas as pd
from typing import Sequence


def compute_completeness(
    df: pd.DataFrame,
    required_columns: Sequence[str],
) -> pd.Series:
    """
    Compute row-level completeness score.

    Completeness is defined as the proportion of required
    columns that are non-null for each row.

    Returns a pandas Series with values between 0.0 and 1.0.
    """
    if df.empty:
        return pd.Series(dtype=float)

    # Safety check: ensure required columns exist
    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Vectorized completeness calculation
    filled = df[required_columns].notna().sum(axis=1)
    return filled / len(required_columns)