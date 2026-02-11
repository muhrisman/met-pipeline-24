import pandas as pd


def compute_coverage(
    df: pd.DataFrame,
    reference_df: pd.DataFrame,
    year_col: str,
    entity_key_col: str,
    value_col: str,
) -> pd.DataFrame:
    """
    Compute coverage (reporting completeness) per year.

    Coverage measures the fraction of expected entities (e.g. kab/kota)
    that have reported data for a given year.

    Parameters
    ----------
    df : pandas.DataFrame
        Reported data.
    reference_df : pandas.DataFrame
        Reference list of all expected entities.
    year_col : str
        Year column name.
    entity_key_col : str
        Normalized entity key column (e.g. kab_kota_key).
    value_col : str
        Column indicating presence of data.

    Returns
    -------
    pandas.DataFrame
        Coverage per year with columns:
        - year
        - coverage
    """

    years = df[year_col].unique()

    expected = (
        reference_df[[entity_key_col]]
        .assign(_key=1)
        .merge(
            pd.DataFrame({year_col: years, "_key": 1}),
            on="_key",
        )
        .drop("_key", axis=1)
    )

    merged = expected.merge(
        df[[entity_key_col, year_col, value_col]],
        on=[entity_key_col, year_col],
        how="left",
    )

    merged["_reported"] = merged[value_col].notna().astype(int)

    coverage = (
        merged.groupby(year_col)["_reported"]
        .mean()
        .reset_index()
        .rename(columns={"_reported": "coverage"})
        .sort_values(year_col)
    )

    return coverage