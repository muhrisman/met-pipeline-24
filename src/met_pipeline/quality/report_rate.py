import pandas as pd
from typing import Union


def _has_report_mask(df: pd.DataFrame, value_col: Union[str, list]) -> pd.Series:
    """Return boolean mask: True if the row has at least one non-null value."""
    if isinstance(value_col, list):
        return df[value_col].notna().any(axis=1)
    return df[value_col].notna()


def compute_report_rate(
    df: pd.DataFrame,
    reference_df: pd.DataFrame,
    year_col: str,
    entity_key_col: str,
    value_col: Union[str, list],
) -> pd.DataFrame:
    """
    Compute report rate (participation rate) per year.

    Report rate = number of entities that submitted data / total expected entities.

    Parameters
    ----------
    df : reported data (e.g. timbulan per kabupaten per year)
    reference_df : master list of all expected entities (kabupaten/kota)
    year_col : column name for year in df
    entity_key_col : normalized key column present in both df and reference_df
    value_col : single column name OR list of columns — a row counts as reported
                if at least one of the specified columns is non-null.
                Use a list for multi-variable datasets (sumber, komposisi).

    Returns
    -------
    DataFrame with columns: year, reported, expected, report_rate
    """
    years = sorted(df[year_col].dropna().unique())
    expected = len(reference_df[entity_key_col].unique())

    rows = []
    for year in years:
        year_df = df[df[year_col] == year]
        mask = _has_report_mask(year_df, value_col)
        reported = year_df[mask][entity_key_col].nunique()
        rows.append({
            year_col: year,
            "reported": reported,
            "expected": expected,
            "report_rate": reported / expected if expected > 0 else 0.0,
        })

    return pd.DataFrame(rows)


def compute_report_rate_by_province(
    df: pd.DataFrame,
    reference_df: pd.DataFrame,
    year_col: str,
    province_col: str,
    entity_key_col: str,
    value_col: Union[str, list],
) -> pd.DataFrame:
    """
    Compute report rate per province per year.

    Parameters
    ----------
    value_col : single column name OR list of columns — a row counts as reported
                if at least one of the specified columns is non-null.
                Use a list for multi-variable datasets (sumber, komposisi).

    Returns
    -------
    DataFrame with columns: year, province, reported, expected, report_rate
    """
    result_rows = []

    for (year, province), group in df.groupby([year_col, province_col]):
        ref_province = reference_df[reference_df[province_col] == province]
        expected = len(ref_province[entity_key_col].unique())
        if expected == 0:
            continue
        mask = _has_report_mask(group, value_col)
        reported = group[mask][entity_key_col].nunique()
        result_rows.append({
            year_col: year,
            province_col: province,
            "reported": reported,
            "expected": expected,
            "report_rate": reported / expected,
        })

    return pd.DataFrame(result_rows).sort_values([year_col, province_col]).reset_index(drop=True)
