import pandas as pd
from pathlib import Path


def normalize_kab_kota(name: str) -> str:
    """
    Normalize kab/kota name for matching purposes.
    """
    if not isinstance(name, str):
        return ""

    return (
        name.lower()
        .replace("kabupaten", "")
        .replace("kab.", "")
        .replace("kota", "")
        .strip()
    )


def load_kab_kota_reference(path: str | Path) -> pd.DataFrame:
    """
    Load the master kab/kota reference list.

    Adds a `kab_kota_key` column used for matching across datasets.
    """
    df = pd.read_csv(path)

    if "kab_kota" not in df.columns:
        raise ValueError("Reference file must contain a 'kab_kota' column")

    df["kab_kota_key"] = df["kab_kota"].apply(normalize_kab_kota)

    return df