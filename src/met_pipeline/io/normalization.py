import re
from typing import Optional


def normalize_kab_kota(name: Optional[str]) -> str:
    """
    Normalize kabupaten/kota names into a canonical key
    that preserves administrative distinction.

    Examples:
    - "Kab. Bandung"        -> "kabupaten_bandung"
    - "Kabupaten Bandung"  -> "kabupaten_bandung"
    - "Kota Bandung"       -> "kota_bandung"
    """

    if not isinstance(name, str):
        return ""

    raw = name.lower()

    # remove punctuation
    raw = re.sub(r"[^\w\s]", " ", raw)

    # tokenize
    tokens = raw.split()

    # detect admin type
    admin = None
    if tokens and tokens[0] in {"kabupaten", "kab"}:
        admin = "kabupaten"
    elif tokens and tokens[0] == "kota":
        admin = "kota"
    else:
        admin = "unknown"

    # remove admin tokens completely
    cleaned_tokens = [
        t for t in tokens
        if t not in {"kabupaten", "kab", "kota", "city"}
    ]

    # rebuild name
    place = " ".join(cleaned_tokens)

    return f"{admin}_{place}"