"""
BPS (Badan Pusat Statistik) data loader via WebAPI.

Requires a BPS WebAPI token from https://webapi.bps.go.id/developer/
Set it as BPS_API_KEY in your .env file.

Usage:
    from met_pipeline.io.bps_loader import BPSClient

    client = BPSClient()  # reads BPS_API_KEY from .env
    df = client.get_pdrb_kabkota(years=[2022, 2023, 2024])
    df = client.get_data(domain="0000", var_id=2533, years=[2024])

API Notes:
    - `th` parameter is REQUIRED for data endpoints and uses internal IDs (th = year - 1900)
    - datacontent keys encode: vervar_id + var_id + turvar_id + th_id + turth_id
    - National domain "0000" has kabkota-level PDRB (var 2533/2534) for 2022+
    - Province domains (e.g. "3200") have per-kabkota breakdowns for older data
"""
import os
import warnings
from typing import List, Optional

import pandas as pd
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


BASE_URL = "https://webapi.bps.go.id/v1/api"

# Discovered BPS variable IDs
KNOWN_VARS = {
    # National domain (0000) — kabkota breakdown via vervar
    "pdrb_hb_kabkota": 2533,       # PDRB Triwulanan Harga Berlaku per Kab/Kota (2022+)
    "pdrb_hk_kabkota": 2534,       # PDRB Triwulanan Harga Konstan per Kab/Kota (2022+)
    "pdrb_distribusi_provinsi": 289,  # Distribusi PDRB per Provinsi

    # Province domain — kabkota breakdown (var IDs vary per province!)
    # Jawa Barat (3200) examples:
    "pdrb_perkapita_hb_3200": 708,  # PDRB per kapita HB
    "pdrb_perkapita_hk_3200": 709,  # PDRB per kapita HK
    "pertumbuhan_pdrb_3200": 48,    # Laju Pertumbuhan PDRB per Kab/Kota
    "jumlah_penduduk_3200": 133,    # Jumlah Penduduk per Kab/Kota (2019-2020)
    "pertumbuhan_penduduk_3200": 136,  # Laju Pertumbuhan Penduduk per Kab/Kota

    # Jawa Timur (3500) examples:
    "pertumbuhan_ekonomi_3500": 527,  # Pertumbuhan Ekonomi per Kab/Kota
}

# PDRB turvar IDs (sectors)
TURVAR_PDRB = {
    2186: "Sektor Primer",
    2187: "Sektor Sekunder",
    2188: "Sektor Tersier",
    2189: "PDRB",  # Total
}

# Turtahun IDs (periods)
TURTAHUN = {
    31: "Triwulan I",
    32: "Triwulan II",
    33: "Triwulan III",
    34: "Triwulan IV",
    35: "Tahunan",
}


def _year_to_th(year: int) -> int:
    """Convert calendar year to BPS th (period) ID."""
    return year - 1900


def _th_to_year(th: int) -> int:
    """Convert BPS th ID to calendar year."""
    return th + 1900


class BPSClient:
    """Client for BPS WebAPI."""

    def __init__(self, token: str = None):
        self.token = token or os.getenv("BPS_API_KEY")
        if not self.token:
            raise ValueError(
                "BPS API token required. Set BPS_API_KEY in .env or pass token= parameter.\n"
                "Register free at https://webapi.bps.go.id/developer/"
            )
        self._session = requests.Session()
        self._session.verify = False  # BPS cert sometimes has issues

    def _get(self, endpoint: str) -> dict:
        """Make authenticated GET request to BPS WebAPI."""
        url = f"{BASE_URL}/{endpoint}/key/{self.token}/"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            resp = self._session.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "Error":
            raise RuntimeError(f"BPS API error: {data.get('message', data)}")
        return data

    # ── Metadata endpoints ──────────────────────────────────────────

    def list_domains(self) -> pd.DataFrame:
        """List all BPS domains (provinces, kabkota)."""
        data = self._get("list/model/domain/perpage/10000/lang/ind")
        return pd.DataFrame(data["data"][1])

    def list_variables(self, domain: str = "0000", keyword: str = None) -> pd.DataFrame:
        """List available statistical variables for a domain, optionally filtered by keyword."""
        kw_part = f"/keyword/{keyword}" if keyword else ""
        page = 1
        all_items = []

        while True:
            data = self._get(
                f"list/model/var/lang/ind/domain/{domain}/page/{page}/perpage/100{kw_part}"
            )
            items = data["data"][1]
            if not items:
                break
            all_items.extend(items)
            pages = data["data"][0].get("pages", 1)
            if page >= pages:
                break
            page += 1

        return pd.DataFrame(all_items)

    def search_variables(self, keyword: str, domain: str = "0000") -> pd.DataFrame:
        """Search variables by keyword using API keyword filter."""
        return self.list_variables(domain=domain, keyword=keyword)

    # ── Data endpoints ──────────────────────────────────────────────

    def get_data(
        self,
        domain: str,
        var_id: int,
        years: List[int],
    ) -> dict:
        """
        Get raw data from BPS dynamic table.

        Parameters
        ----------
        domain : BPS domain code ("0000" for national, "3200" for province, etc.)
        var_id : variable ID
        years : list of calendar years (e.g. [2022, 2023, 2024])

        Returns
        -------
        dict with keys: datacontent, vervar, turvar, tahun, turtahun (all as dicts)
        """
        # BPS API limits th to max 2 years per request, so batch if needed
        MAX_TH = 2
        year_batches = [years[i:i + MAX_TH] for i in range(0, len(years), MAX_TH)]

        merged = {
            "datacontent": {},
            "vervar": {},
            "turvar": {},
            "tahun": {},
            "turtahun": {},
            "var": [],
            "status": "OK",
        }

        for batch in year_batches:
            th_str = ";".join(str(_year_to_th(y)) for y in batch)
            data = self._get(
                f"list/model/data/lang/ind/domain/{domain}/var/{var_id}/th/{th_str}"
            )
            dc = data.get("datacontent", {})
            if isinstance(dc, dict):
                merged["datacontent"].update(dc)
            for field in ["vervar", "turvar", "tahun", "turtahun"]:
                for v in data.get(field, []):
                    if v:
                        merged[field][v["val"]] = v["label"]
            if not merged["var"]:
                merged["var"] = data.get("var", [])

        return merged

    def parse_datacontent(self, raw: dict, var_id: int) -> pd.DataFrame:
        """
        Parse BPS datacontent dict into a tidy DataFrame.

        The datacontent key format is: vervar_id + var_id + turvar_id + th_id + turth_id
        (concatenated as strings with varying lengths).
        """
        dc = raw["datacontent"]
        if not dc or not isinstance(dc, dict):
            return pd.DataFrame()

        vervar_map = {int(k): v for k, v in raw["vervar"].items()}
        turvar_map = {int(k): v for k, v in raw["turvar"].items()}
        tahun_map = {int(k): v for k, v in raw["tahun"].items()}
        turtahun_map = {int(k): v for k, v in raw["turtahun"].items()}

        var_str = str(var_id)
        var_len = len(var_str)

        rows = []
        for key_str, value in dc.items():
            # Find var_id position in the key
            var_pos = key_str.find(var_str)
            if var_pos < 0:
                continue

            vervar_id = key_str[:var_pos]
            rest = key_str[var_pos + var_len:]

            # rest = turvar_id + th_id + turth_id
            # turvar IDs are typically 4 digits (or 1 digit "0")
            # th IDs are 3 digits, turth IDs are 1-2 digits
            # Try to parse from the end: last 1-2 digits = turth, before that 3 digits = th
            if len(rest) >= 4:
                turth_id = rest[-2:] if len(rest) > 4 else rest[-1:]
                th_end = len(rest) - len(turth_id)
                th_id = rest[th_end - 3:th_end]
                turvar_id = rest[:th_end - 3] if th_end > 3 else "0"
            else:
                turvar_id = "0"
                th_id = rest
                turth_id = "0"

            rows.append({
                "vervar_id": vervar_id,
                "vervar": vervar_map.get(int(vervar_id), vervar_id) if vervar_id.isdigit() else vervar_id,
                "turvar_id": turvar_id,
                "turvar": turvar_map.get(int(turvar_id), turvar_id) if turvar_id.isdigit() else turvar_id,
                "tahun": tahun_map.get(int(th_id), str(_th_to_year(int(th_id)))) if th_id.isdigit() else th_id,
                "periode": turtahun_map.get(int(turth_id), turth_id) if turth_id.isdigit() else turth_id,
                "value": value,
            })

        return pd.DataFrame(rows)

    # ── Convenience methods ─────────────────────────────────────────

    def get_pdrb_kabkota(
        self,
        years: List[int] = None,
        harga: str = "berlaku",
        periode: str = "Tahunan",
        sektor: str = "PDRB",
    ) -> pd.DataFrame:
        """
        Get PDRB data for all 514 kabkota from national domain.

        Parameters
        ----------
        years : list of years (default: [2022, 2023, 2024])
        harga : "berlaku" (current prices) or "konstan" (constant 2010 prices)
        periode : "Tahunan" or "Triwulan I/II/III/IV"
        sektor : "PDRB" (total), "Sektor Primer", "Sektor Sekunder", "Sektor Tersier"

        Returns
        -------
        DataFrame with columns: kabkota_id, kabkota, tahun, pdrb
        """
        if years is None:
            years = [2022, 2023, 2024]

        var_id = KNOWN_VARS["pdrb_hb_kabkota"] if harga == "berlaku" else KNOWN_VARS["pdrb_hk_kabkota"]
        raw = self.get_data(domain="0000", var_id=var_id, years=years)
        df = self.parse_datacontent(raw, var_id)

        if df.empty:
            return df

        # Filter by sektor and periode
        if sektor:
            df = df[df["turvar"] == sektor]
        if periode:
            df = df[df["periode"] == periode]

        result = df[["vervar_id", "vervar", "tahun", "value"]].copy()
        result.columns = ["kabkota_id", "kabkota", "tahun", "pdrb"]
        result["tahun"] = result["tahun"].astype(int)
        return result.sort_values(["kabkota_id", "tahun"]).reset_index(drop=True)

    def get_pdrb_growth_kabkota(self, years: List[int] = None) -> pd.DataFrame:
        """
        Compute PDRB growth rate (YoY) for all kabkota using PDRB Harga Konstan.

        Returns DataFrame with: kabkota_id, kabkota, tahun, pdrb_hk, pdrb_growth_pct
        """
        if years is None:
            years = [2022, 2023, 2024]

        # Need year before earliest for growth calculation
        all_years = sorted(set([min(years) - 1] + list(years)))
        # Filter to available range (2022+)
        all_years = [y for y in all_years if y >= 2022]

        pdrb = self.get_pdrb_kabkota(years=all_years, harga="konstan")
        if pdrb.empty:
            return pdrb

        pdrb = pdrb.sort_values(["kabkota_id", "tahun"])
        pdrb["pdrb_hk"] = pdrb["pdrb"]
        pdrb["pdrb_prev"] = pdrb.groupby("kabkota_id")["pdrb_hk"].shift(1)
        pdrb["pdrb_growth_pct"] = ((pdrb["pdrb_hk"] - pdrb["pdrb_prev"]) / pdrb["pdrb_prev"]) * 100

        # Filter to requested years only
        result = pdrb[pdrb["tahun"].isin(years)][
            ["kabkota_id", "kabkota", "tahun", "pdrb_hk", "pdrb_growth_pct"]
        ].copy()
        return result.reset_index(drop=True)


def discover_economic_variables(token: str = None) -> pd.DataFrame:
    """
    Discover all economic-related BPS variables at national level.

    Returns DataFrame with matching variables for economic indicators.
    """
    client = BPSClient(token=token)
    keywords = ["PDRB", "Pertumbuhan", "Penduduk", "Kepadatan", "Kemiskinan", "IPM"]
    results = []
    for kw in keywords:
        try:
            df = client.search_variables(kw)
            if not df.empty:
                df["search_keyword"] = kw
                results.append(df)
        except Exception as e:
            print(f"Warning: search '{kw}' failed: {e}")
    if results:
        return pd.concat(results, ignore_index=True)
    return pd.DataFrame()
