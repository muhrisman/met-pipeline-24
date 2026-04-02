import pandas as pd

# Default weights per dataset, from roadmap formulas and notebook implementation
WEIGHTS = {
    "timbulan": {"report_rate": 0.6, "completeness": 0.0, "outlier": 0.4},
    "sumber":   {"report_rate": 0.3, "completeness": 0.4, "outlier": 0.3},
    "komposisi": {"report_rate": 0.4, "completeness": 0.3, "outlier": 0.3},
}


def compute_quality_score(
    df: pd.DataFrame,
    dataset: str = None,
    report_rate_col: str = "Report_Rate",
    completeness_col: str = "Completeness",
    outlier_quality_col: str = "outlier_quality_score",
    weights: dict = None,
    score_col: str = "quality_score",
) -> pd.DataFrame:
    """
    Compute weighted quality score per row.

    Weights can be provided directly or by specifying a dataset name
    ('timbulan', 'sumber', 'komposisi') to use the default weights.

    Default formulas (from roadmap):
    - Timbulan:  0.6 * report_rate + 0.4 * outlier_quality
    - Sumber:    0.3 * report_rate + 0.4 * completeness + 0.3 * outlier_quality
    - Komposisi: 0.4 * report_rate + 0.3 * completeness + 0.3 * outlier_quality

    Parameters
    ----------
    df : DataFrame with metric columns
    dataset : 'timbulan', 'sumber', or 'komposisi' — selects default weights
    report_rate_col : column name for report rate (0–1)
    completeness_col : column name for completeness (0–1), used when weight > 0
    outlier_quality_col : column name for outlier quality score (0–1)
    weights : custom weights dict with keys 'report_rate', 'completeness', 'outlier'
    score_col : name of output score column

    Returns
    -------
    DataFrame with added columns:
    - score_col: final quality score (0–1)
    - score_col + '_0_10': score on 0–10 scale
    """
    if weights is None:
        if dataset is None:
            raise ValueError("Provide either 'dataset' name or 'weights' dict.")
        if dataset not in WEIGHTS:
            raise ValueError(f"Unknown dataset '{dataset}'. Choose from: {list(WEIGHTS.keys())}")
        weights = WEIGHTS[dataset]

    w_report = weights.get("report_rate", 0)
    w_complete = weights.get("completeness", 0)
    w_outlier = weights.get("outlier", 0)

    result = df.copy()

    # Fill missing inputs with neutral values
    report_rate = result[report_rate_col].fillna(0) if report_rate_col in result.columns else 0
    outlier_quality = result[outlier_quality_col].fillna(1) if outlier_quality_col in result.columns else 1

    score = w_report * report_rate + w_outlier * outlier_quality

    if w_complete > 0:
        if completeness_col not in result.columns:
            raise ValueError(
                f"completeness_col '{completeness_col}' not found but weight={w_complete}. "
                "Provide completeness data or set weight to 0."
            )
        completeness = result[completeness_col].fillna(0)
        score = score + w_complete * completeness

    result[score_col] = score
    result[score_col + "_0_10"] = score * 10

    return result


def compute_quality_score_timbulan(
    report_rate_df: pd.DataFrame,
    outlier_df: pd.DataFrame,
    merge_on: list = None,
) -> pd.DataFrame:
    """
    Compute quality score for Timbulan dataset.

    Merges report rate and outlier quality DataFrames, then applies
    the Timbulan formula: 0.6 * report_rate + 0.4 * outlier_quality

    Parameters
    ----------
    report_rate_df : output of compute_report_rate_by_province()
                     must have 'report_rate' column
    outlier_df : output of aggregate_outlier_quality()
                 must have 'outlier_quality_score' column
    merge_on : list of columns to merge on (default: ['Provinsi', 'Tahun'])
    """
    if merge_on is None:
        merge_on = ["Provinsi", "Tahun"]

    merged = report_rate_df.merge(
        outlier_df[merge_on + ["outlier_quality_score"]],
        on=merge_on,
        how="left",
    )
    merged["outlier_quality_score"] = merged["outlier_quality_score"].fillna(1)

    return compute_quality_score(
        merged,
        dataset="timbulan",
        report_rate_col="report_rate",
        outlier_quality_col="outlier_quality_score",
    )


def compute_quality_score_sumber(
    report_rate_df: pd.DataFrame,
    completeness_df: pd.DataFrame,
    outlier_df: pd.DataFrame,
    merge_on: list = None,
) -> pd.DataFrame:
    """
    Compute quality score for Sumber Sampah dataset.

    Formula: 0.3 * report_rate + 0.4 * completeness + 0.3 * outlier_quality
    """
    if merge_on is None:
        merge_on = ["Provinsi", "Tahun"]

    merged = (
        report_rate_df
        .merge(completeness_df[merge_on + ["Completeness"]], on=merge_on, how="left")
        .merge(outlier_df[merge_on + ["outlier_quality_score"]], on=merge_on, how="left")
    )

    return compute_quality_score(
        merged,
        dataset="sumber",
        report_rate_col="report_rate",
        completeness_col="Completeness",
        outlier_quality_col="outlier_quality_score",
    )


def compute_quality_score_komposisi(
    report_rate_df: pd.DataFrame,
    completeness_df: pd.DataFrame,
    outlier_df: pd.DataFrame,
    merge_on: list = None,
) -> pd.DataFrame:
    """
    Compute quality score for Komposisi Sampah dataset.

    Formula: 0.4 * report_rate + 0.3 * completeness + 0.3 * outlier_quality
    """
    if merge_on is None:
        merge_on = ["Provinsi", "Tahun"]

    merged = (
        report_rate_df
        .merge(completeness_df[merge_on + ["Completeness"]], on=merge_on, how="left")
        .merge(outlier_df[merge_on + ["outlier_quality_score"]], on=merge_on, how="left")
    )

    return compute_quality_score(
        merged,
        dataset="komposisi",
        report_rate_col="report_rate",
        completeness_col="Completeness",
        outlier_quality_col="outlier_quality_score",
    )
