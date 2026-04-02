import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


def detect_outliers_iqr(
    df: pd.DataFrame,
    col: str,
    group_col: str = None,
) -> pd.DataFrame:
    """
    Detect outliers using IQR method.

    If group_col is provided, computes IQR bounds per group (e.g. per province).
    Otherwise computes a single global bound.

    Returns the input DataFrame with two added columns:
    - 'anomaly_flag': 1 = normal, -1 = outlier
    - 'anomaly_score': 0.0 (normal) to 1.0 (extreme outlier) based on distance from bounds
    """
    result = df.copy()
    result["anomaly_flag"] = 1
    result["anomaly_score"] = 0.0

    valid_mask = result[col].notna()

    if group_col:
        for group, idx in result[valid_mask].groupby(group_col).groups.items():
            values = result.loc[idx, col]
            flags, scores = _iqr_flags(values)
            result.loc[idx, "anomaly_flag"] = flags
            result.loc[idx, "anomaly_score"] = scores
    else:
        values = result.loc[valid_mask, col]
        flags, scores = _iqr_flags(values)
        result.loc[valid_mask, "anomaly_flag"] = flags
        result.loc[valid_mask, "anomaly_score"] = scores

    return result


def _iqr_flags(values: pd.Series):
    Q1 = values.quantile(0.25)
    Q3 = values.quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR

    is_outlier = (values < lower) | (values > upper)
    flags = np.where(is_outlier, -1, 1)

    # Score: how far beyond the bound, normalized 0-1
    distance = pd.Series(0.0, index=values.index)
    if IQR > 0:
        below = (lower - values).clip(lower=0)
        above = (values - upper).clip(lower=0)
        distance = (below + above) / IQR
        distance = distance.clip(upper=1.0)

    return flags, distance.values


def detect_outliers_iforest(
    df: pd.DataFrame,
    col: str,
    group_col: str = None,
    contamination: float = 0.05,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Detect outliers using Isolation Forest.

    If group_col is provided, fits a separate model per group (e.g. per province or per year).
    Otherwise fits a single global model.

    Returns the input DataFrame with two added columns:
    - 'anomaly_flag': 1 = normal, -1 = outlier  (sklearn convention)
    - 'anomaly_score': 0.0 (normal) to 1.0 (most anomalous), normalized from raw IF scores
    """
    result = df.copy()
    result["anomaly_flag"] = np.nan
    result["anomaly_score"] = np.nan

    valid_mask = result[col].notna()

    if group_col:
        for group, idx in result[valid_mask].groupby(group_col).groups.items():
            subset = result.loc[idx, [col]]
            if len(subset) < 2:
                result.loc[idx, "anomaly_flag"] = 1
                result.loc[idx, "anomaly_score"] = 0.0
                continue
            flags, scores = _iforest_flags(subset, contamination, random_state)
            result.loc[idx, "anomaly_flag"] = flags
            result.loc[idx, "anomaly_score"] = scores
    else:
        subset = result.loc[valid_mask, [col]]
        flags, scores = _iforest_flags(subset, contamination, random_state)
        result.loc[valid_mask, "anomaly_flag"] = flags
        result.loc[valid_mask, "anomaly_score"] = scores

    # Rows with NaN (no data in col) stay NaN — fill with neutral values
    result["anomaly_flag"] = result["anomaly_flag"].fillna(1)
    result["anomaly_score"] = result["anomaly_score"].fillna(0.0)

    return result


def _iforest_flags(subset: pd.DataFrame, contamination: float, random_state: int):
    iso = IsolationForest(contamination=contamination, random_state=random_state)
    iso.fit(subset)
    flags = iso.predict(subset)  # 1 = normal, -1 = anomaly

    # Normalize raw scores to 0-1 (higher = more anomalous)
    raw_scores = iso.decision_function(subset)  # higher = more normal
    # Invert and normalize: anomalous → high score
    scores = -raw_scores
    min_s, max_s = scores.min(), scores.max()
    if max_s > min_s:
        scores = (scores - min_s) / (max_s - min_s)
    else:
        scores = np.zeros_like(scores)

    return flags, scores


def detect_outliers_panel_iforest(
    df: pd.DataFrame,
    value_col: str,
    entity_col: str,
    year_col: str,
    contamination: float = 0.05,
    n_estimators: int = 300,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Multi-feature Isolation Forest for panel data (entity × year).

    Uses two features as implemented in explore_analysis.ipynb:
    - log(value + 1): scale-adjusted level
    - growth_rate: YoY % change, only for consecutive years (else 0)

    This is the recommended method for timbulan data since it captures
    both magnitude outliers and sudden change outliers simultaneously.

    Parameters
    ----------
    df : panel DataFrame sorted by entity and year
    value_col : the metric column (e.g. 'jml_timbulan_tahun')
    entity_col : kabupaten/kota column (e.g. 'Kabupaten/Kota')
    year_col : year column (e.g. 'Tahun')
    contamination : expected fraction of outliers
    n_estimators : number of trees in the forest

    Returns
    -------
    DataFrame with added columns:
    - 'log_value': log1p transformed value
    - 'growth_rate': YoY growth (0 for non-consecutive years)
    - 'anomaly_flag': 1 = normal, -1 = outlier
    - 'anomaly_score': 0.0 (normal) to 1.0 (most anomalous)
    """
    result = df.copy()
    result = result.sort_values([entity_col, year_col])

    # Log transformation
    result["log_value"] = np.log1p(result[value_col].fillna(0))

    # Consecutive-year growth rate only
    result["prev_year"] = result.groupby(entity_col)[year_col].shift(1)
    result["prev_value"] = result.groupby(entity_col)[value_col].shift(1)

    result["growth_rate"] = np.where(
        result[year_col] - result["prev_year"] == 1,
        (result[value_col] - result["prev_value"]) / result["prev_value"],
        np.nan,
    )
    result["growth_rate"] = (
        result["growth_rate"]
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0)
    )
    result = result.drop(columns=["prev_year", "prev_value"])

    # Only run on rows with actual data
    valid_mask = result[value_col].notna()
    features = result.loc[valid_mask, ["log_value", "growth_rate"]]

    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    iso = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=random_state,
    )
    flags = iso.fit_predict(features_scaled)
    raw_scores = iso.decision_function(features_scaled)

    # Normalize anomaly score 0-1 (higher = more anomalous)
    scores = -raw_scores
    min_s, max_s = scores.min(), scores.max()
    if max_s > min_s:
        scores = (scores - min_s) / (max_s - min_s)
    else:
        scores = np.zeros_like(scores)

    result["anomaly_flag"] = 1
    result["anomaly_score"] = 0.0
    result.loc[valid_mask, "anomaly_flag"] = flags
    result.loc[valid_mask, "anomaly_score"] = scores

    return result


def detect_outliers_multifeature_iforest(
    df: pd.DataFrame,
    feature_cols: list,
    year_col: str = None,
    log_transform: bool = False,
    fill_na: float = 0.0,
    contamination: float = 0.05,
    min_samples: int = 10,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Multi-column Isolation Forest, optionally grouped per year.

    Used for Sumber and Komposisi datasets:
    - Sumber (notebook cell 80): log_transform=True, year_col=None (global model)
      Features: log1p of each sumber variable + log1p of total
    - Komposisi (notebook cell 99): log_transform=False, year_col='Tahun' (per-year model)
      Features: 9 raw composition percentages (NaN filled with 0)

    Parameters
    ----------
    df : DataFrame with feature columns already present
    feature_cols : list of columns to use as IForest features
    year_col : if provided, fits a separate model per year
    log_transform : if True, applies log1p to all feature columns before scaling
    fill_na : fill NaN values in feature_cols with this value before running
    contamination : expected fraction of outliers
    min_samples : skip group if fewer rows than this (marks all as normal)
    random_state : random seed

    Returns
    -------
    DataFrame with added columns:
    - 'anomaly_flag': 1 = normal, -1 = outlier
    - 'anomaly_score': 0.0 (normal) to 1.0 (most anomalous)
    """
    result = df.copy()
    result["anomaly_flag"] = 1
    result["anomaly_score"] = 0.0

    # Only run on rows with at least one non-null feature
    valid_mask = result[feature_cols].notna().any(axis=1)
    working = result.loc[valid_mask, feature_cols].fillna(fill_na)

    if log_transform:
        working = np.log1p(working)

    if year_col is None:
        # Single global model
        if len(working) >= min_samples:
            flags, scores = _multifeature_iforest_flags(working, contamination, random_state)
            result.loc[valid_mask, "anomaly_flag"] = flags
            result.loc[valid_mask, "anomaly_score"] = scores
    else:
        # Per-year model
        for year, idx in result.loc[valid_mask].groupby(year_col).groups.items():
            subset = working.loc[idx]
            if len(subset) < min_samples:
                continue
            flags, scores = _multifeature_iforest_flags(subset, contamination, random_state)
            result.loc[idx, "anomaly_flag"] = flags
            result.loc[idx, "anomaly_score"] = scores

    return result


def _multifeature_iforest_flags(subset: pd.DataFrame, contamination: float, random_state: int):
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(subset)

    iso = IsolationForest(contamination=contamination, random_state=random_state)
    flags = iso.fit_predict(X_scaled)

    raw_scores = iso.decision_function(X_scaled)
    scores = -raw_scores
    min_s, max_s = scores.min(), scores.max()
    if max_s > min_s:
        scores = (scores - min_s) / (max_s - min_s)
    else:
        scores = np.zeros_like(scores)

    return flags, scores


def aggregate_outlier_quality(
    df: pd.DataFrame,
    group_cols: list,
) -> pd.DataFrame:
    """
    Aggregate anomaly flags to group level (e.g. province × year).

    Returns DataFrame with:
    - group_cols
    - anomaly_rate: fraction of outliers in group
    - outlier_quality_score: 1 - anomaly_rate (higher = better quality)
    """
    if "anomaly_flag" not in df.columns:
        raise ValueError("DataFrame must have 'anomaly_flag' column.")

    result = (
        df.groupby(group_cols)
        .apply(lambda g: pd.Series({
            "total": len(g),
            "outlier_count": (g["anomaly_flag"] == -1).sum(),
            "anomaly_rate": (g["anomaly_flag"] == -1).mean(),
        }), include_groups=False)
        .reset_index()
    )
    result["outlier_quality_score"] = 1 - result["anomaly_rate"]
    return result


def summarize_outliers(
    df: pd.DataFrame,
    group_col: str,
) -> pd.DataFrame:
    """
    Summarize outlier counts and ratio per group.

    Expects df to have 'anomaly_flag' column (-1 = outlier, 1 = normal).

    Returns a DataFrame with columns:
    - group_col
    - total: total non-null rows
    - outlier_count: number of outliers
    - outlier_ratio: outlier_count / total (0.0 - 1.0)
    - quality_score: 1 - outlier_ratio (higher = better quality)
    """
    if "anomaly_flag" not in df.columns:
        raise ValueError("DataFrame must have 'anomaly_flag' column. Run detect_outliers_* first.")

    summary = (
        df.groupby(group_col)
        .apply(lambda g: pd.Series({
            "total": len(g),
            "outlier_count": (g["anomaly_flag"] == -1).sum(),
        }), include_groups=False)
        .reset_index()
    )
    summary["outlier_ratio"] = summary["outlier_count"] / summary["total"]
    summary["quality_score"] = 1 - summary["outlier_ratio"]
    return summary.sort_values("outlier_ratio", ascending=False).reset_index(drop=True)
