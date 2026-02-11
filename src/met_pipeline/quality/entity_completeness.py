import pandas as pd


def compute_entity_completeness(
    df: pd.DataFrame,
    reference_df: pd.DataFrame,
    year_col: str,
    province_col: str,
    entity_key_col: str,
    value_col: str,
) -> pd.DataFrame:
    """
    Compute entity-level completeness by merging reported data
    with a reference list of expected entities.

    Returns a DataFrame with one row per entity per year,
    including a binary completeness flag.
    """

    years = df[year_col].unique()

    expected = (
        reference_df[[province_col, entity_key_col]]
        .assign(_key=1)
        .merge(
            pd.DataFrame({year_col: years, "_key": 1}),
            on="_key",
        )
        .drop("_key", axis=1)
    )

    merged = expected.merge(
        df[
            [
                year_col,
                province_col,
                entity_key_col,
                value_col,
            ]
        ],
        on=[year_col, province_col, entity_key_col],
        how="left",
    )

    merged["completeness"] = merged[value_col].notna().astype(int)

    return merged