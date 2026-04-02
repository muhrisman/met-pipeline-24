"""
Dashboard Clustering Persampahan Kabupaten/Kota 2024
Streamlit interactive app
"""

import warnings
warnings.filterwarnings("ignore")

import re
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import geopandas as gpd

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Cluster Persampahan 2024",
    page_icon=None,
    layout="wide",
)

# ── Load data ────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("data/output/cluster_economic_sumber_2024.csv")
    return df

@st.cache_data
def load_quality():
    return pd.read_csv("data/output/quality_score_2024.csv")

GEOJSON_URL = "https://raw.githubusercontent.com/superpikar/indonesia-geojson/master/indonesia-en.geojson"

@st.cache_data
def load_geo():
    import requests, tempfile, os

    # Try local shapefile first (development), fall back to public GeoJSON (production)
    local_shp = "notebooks/shp/DUKCAPIL_KAB.shp"
    if os.path.exists(local_shp):
        gdf = gpd.read_file(local_shp)
        gdf = gdf[["nama_prop", "nama_kab", "geometry"]].copy()
        gdf = gdf.rename(columns={"nama_prop": "nama_prop", "nama_kab": "nama_kab"})
    else:
        resp = requests.get(GEOJSON_URL, timeout=60)
        resp.raise_for_status()
        with tempfile.NamedTemporaryFile(suffix=".geojson", delete=False, mode="w") as f:
            f.write(resp.text)
            tmp_path = f.name
        gdf = gpd.read_file(tmp_path)
        os.unlink(tmp_path)
        # Map column names from public GeoJSON to expected names
        gdf = gdf.rename(columns={
            "state": "nama_prop",
            "name": "nama_kab",
        })
        if "nama_prop" not in gdf.columns:
            gdf["nama_prop"] = ""
        if "nama_kab" not in gdf.columns:
            gdf["nama_kab"] = gdf.get("NAME_2", gdf.get("name", ""))
        gdf = gdf[["nama_prop", "nama_kab", "geometry"]].copy()

    gdf["geometry"] = gdf["geometry"].simplify(0.01, preserve_topology=True)
    gdf["nama_kab_norm"] = (
        gdf["nama_kab"]
        .str.strip()
        .str.upper()
        .str.replace(r"^KAB\.\s*", "", regex=True)
        .str.replace(r"^KOTA\s+", "KOTA ", regex=True)
        .str.strip()
    )
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    else:
        gdf = gdf.to_crs(epsg=4326)
    return gdf

@st.cache_data
def build_geojson(_gdf, cluster_keys: tuple):
    """Cache GeoJSON export — only recomputes when cluster filter changes."""
    import json
    _gdf = _gdf.copy()
    _gdf["id"] = _gdf.index.astype(str)
    return json.loads(_gdf.to_json()), _gdf["id"].tolist()

df = load_data()
gdf = load_geo()
dq = load_quality()

# ── Cluster color palette ────────────────────────────────────────────────────
CLUSTER_COLORS = {
    0: "#2ecc71",
    1: "#e74c3c",
    2: "#3498db",
    3: "#f39c12",
    4: "#9b59b6",
}

FEATURE_LABELS = {
    "rumah_tangga_per1k": "Rumah Tangga /1K",
    "perkantoran_per1k": "Perkantoran /1K",
    "perniagaan_per1k": "Perniagaan /1K",
    "pasar_per1k": "Pasar /1K",
    "fasilitas_publik_per1k": "Fasilitas Publik /1K",
    "lainnya_per1k": "Lainnya /1K",
    "kawasan_per1k": "Kawasan /1K",
    "pdrb_perkapita_juta": "PDRB/Kapita (Juta)",
    "pdrb_growth_pct": "PDRB Growth (%)",
    "kepadatan": "Kepadatan (jiwa/km²)",
    "is_urban": "Urban/Rural",
    "fasilitas_per100k": "Fasilitas /100K",
    "sampah_dikelola_per1k": "Sampah Dikelola /1K",
    "timbulan_per1k": "Timbulan /1K",
}

SUMBER_PER1K = [
    "rumah_tangga_per1k", "perkantoran_per1k", "perniagaan_per1k",
    "pasar_per1k", "fasilitas_publik_per1k", "lainnya_per1k", "kawasan_per1k",
]

FEATURE_ECON = ["pdrb_perkapita_juta", "pdrb_growth_pct"]
FEATURE_DEMOGRAFI = ["kepadatan", "is_urban"]
FEATURE_FAS = ["fasilitas_per100k", "sampah_dikelola_per1k"]
FEATURE_TIM = ["timbulan_per1k"]

ALL_FEATURES = SUMBER_PER1K + FEATURE_ECON + FEATURE_DEMOGRAFI + FEATURE_FAS + FEATURE_TIM

# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.title("Filter")

all_labels = df.sort_values("cluster")["cluster_label"].unique().tolist()
cluster_options = {f"Cluster {c}: {df[df['cluster']==c]['cluster_label'].iloc[0]}": c
                   for c in sorted(df["cluster"].unique())}
selected_cluster_labels = st.sidebar.selectbox(
    "Cluster",
    options=["Semua"] + list(cluster_options.keys()),
)
if selected_cluster_labels == "Semua":
    selected_clusters = list(cluster_options.values())
else:
    selected_clusters = [cluster_options[selected_cluster_labels]]

all_provinsi = sorted(df["provinsi"].unique())
selected_provinsi_opt = st.sidebar.selectbox(
    "Provinsi", options=["Semua"] + all_provinsi
)
selected_provinsi = all_provinsi if selected_provinsi_opt == "Semua" else [selected_provinsi_opt]

ukuran_options = ["kecil", "sedang", "besar", "metropolitan"]
selected_ukuran_opt = st.sidebar.selectbox(
    "Ukuran Kota", options=["Semua"] + ukuran_options
)
selected_ukuran = ukuran_options if selected_ukuran_opt == "Semua" else [selected_ukuran_opt]

show_anomali = st.sidebar.checkbox("Tampilkan anomali", value=True)

st.sidebar.divider()
st.sidebar.caption(
    f"K-Means (K=5) pada {len(ALL_FEATURES)} fitur. "
    f"Anomali: Isolation Forest (5%). "
    f"Similarity: Euclidean distance. "
    f"Data: SIPSN & BPS 2024."
)

# Apply filters
mask = (
    df["cluster"].isin(selected_clusters)
    & df["provinsi"].isin(selected_provinsi)
    & df["ukuran_kota"].isin(selected_ukuran)
)
if not show_anomali:
    mask &= ~df["is_anomali"].astype(bool)
dff = df[mask].copy()

# Filter indicator in sidebar
total = len(df)
filtered = len(dff)
if filtered == total:
    st.sidebar.info(f"Menampilkan semua {total} kabkota")
elif filtered == 0:
    st.sidebar.error("Tidak ada data yang cocok dengan filter ini.")
else:
    st.sidebar.success(f"Filter aktif: {filtered} dari {total} kabkota")

st.sidebar.divider()
st.sidebar.markdown("**Metodologi**")
st.sidebar.caption(
    f"K-Means (K=5) pada {len(ALL_FEATURES)} fitur. "
    f"Anomali: Isolation Forest (5%). "
    f"Similarity: Euclidean distance. "
    f"Data: SIPSN & BPS 2024."
)

if filtered == 0:
    st.warning("Tidak ada data yang cocok dengan filter yang dipilih. Silakan ubah filter.")
    st.stop()

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Ringkasan", "Peta Cluster", "Profil Cluster", "Cari Kabkota", "Kualitas Data"])

# ═══════════════════════════════════════════════════════════════════
# TAB 1 — RINGKASAN
# ═══════════════════════════════════════════════════════════════════
with tab1:
    st.title("Dashboard Cluster Persampahan Kabupaten/Kota 2024")
    st.caption("Sumber: SIPSN, BPS. Metode: K-Means (K=5), 14 fitur. Anomali: Isolation Forest.")

    # Metric row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Kabkota", len(dff))
    col2.metric("Jumlah Cluster", dff["cluster"].nunique())
    col3.metric("Rata-rata Silhouette", f"{dff['silhouette'].mean():.4f}")
    col4.metric("Data Anomali", int(dff["is_anomali"].sum()))

    st.divider()

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Distribusi Cluster")
        cluster_summary = (
            dff.groupby(["cluster", "cluster_label"])
            .size()
            .reset_index(name="jumlah")
            .sort_values("cluster")
        )
        cluster_summary["color"] = cluster_summary["cluster"].map(CLUSTER_COLORS)
        cluster_summary["label"] = cluster_summary.apply(
            lambda r: f"Cluster {r['cluster']}: {r['cluster_label']}", axis=1
        )
        fig_pie = px.pie(
            cluster_summary,
            values="jumlah",
            names="label",
            color="cluster",
            color_discrete_map={c: CLUSTER_COLORS[c] for c in CLUSTER_COLORS},
            hole=0.4,
        )
        fig_pie.update_traces(textinfo="value+percent")
        fig_pie.update_layout(height=350, showlegend=True, margin=dict(t=10, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_right:
        st.subheader("Distribusi Ukuran Kota per Cluster")
        cross = pd.crosstab(dff["cluster_label"], dff["ukuran_kota"])
        cross = cross.reindex(columns=[c for c in ukuran_options if c in cross.columns])
        fig_bar = px.bar(
            cross.reset_index().melt(id_vars="cluster_label", var_name="Ukuran", value_name="Jumlah"),
            x="cluster_label", y="Jumlah", color="Ukuran",
            barmode="stack",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_bar.update_layout(height=350, xaxis_title="", margin=dict(t=10, b=10))
        st.plotly_chart(fig_bar, use_container_width=True)

    # Summary table
    st.subheader("Ringkasan Statistik per Cluster")
    summary = dff.groupby(["cluster", "cluster_label"]).agg(
        Jumlah=("kabkota", "count"),
        Populasi_Rata=("populasi", "mean"),
        PDRB_Rata=("pdrb_perkapita_juta", "mean"),
        Kepadatan_Rata=("kepadatan", "mean"),
        Timbulan_Rata=("timbulan_per1k", "mean"),
        Sampah_Dikelola=("sampah_dikelola_per1k", "mean"),
        Anomali=("is_anomali", "sum"),
        Silhouette=("silhouette", "mean"),
    ).round(2).reset_index()
    summary["Anomali"] = summary["Anomali"].astype(int)
    summary.columns = [
        "Cluster", "Label", "Jumlah", "Populasi Rata-rata",
        "PDRB/Kapita (Juta)", "Kepadatan", "Timbulan/1K",
        "Dikelola/1K", "Anomali", "Silhouette"
    ]
    st.dataframe(summary, use_container_width=True, hide_index=True)

    # Download filtered data
    st.download_button(
        label="Download data (CSV)",
        data=dff.to_csv(index=False).encode("utf-8"),
        file_name="cluster_filtered.csv",
        mime="text/csv",
    )


# ═══════════════════════════════════════════════════════════════════
# TAB 2 — PETA
# ═══════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Peta Sebaran Cluster Kabupaten/Kota")

    # Normalize cluster data names to join with shapefile
    df_map = dff.copy()
    df_map["nama_kab_norm"] = (
        df_map["kabkota"]
        .str.strip()
        .str.upper()
    )

    # Join with geodataframe
    gdf_joined = gdf.merge(
        df_map[["nama_kab_norm", "cluster", "cluster_label", "provinsi",
                "populasi", "pdrb_perkapita_juta", "timbulan_per1k", "silhouette", "is_anomali"]],
        on="nama_kab_norm",
        how="left",
    )

    gdf_joined["cluster_str"] = gdf_joined["cluster"].apply(
        lambda c: f"Cluster {int(c)}: {gdf_joined[gdf_joined['cluster']==c]['cluster_label'].iloc[0]}"
        if pd.notna(c) else "Tidak ada data"
    )
    gdf_joined["color"] = gdf_joined["cluster"].map(CLUSTER_COLORS).fillna("#bdc3c7")

    # Split clustered vs missing
    gdf_clustered = gdf_joined[gdf_joined["cluster"].notna()].copy()
    gdf_missing   = gdf_joined[gdf_joined["cluster"].isna()].copy()

    # Build GeoJSON only for clustered kabkota
    cluster_key = tuple(gdf_clustered["cluster"].astype(str).tolist())
    geojson_all, id_list_all = build_geojson(gdf_joined, cluster_key)
    gdf_plot = gdf_joined.copy()
    gdf_plot["id"] = id_list_all

    # Filter geojson features to clustered only
    clustered_ids = set(
        gdf_plot[gdf_plot["cluster"].notna()]["id"].tolist()
    )
    geojson_clustered = {
        "type": "FeatureCollection",
        "features": [
            f for f in geojson_all["features"]
            if str(f.get("properties", {}).get("id", "")) in clustered_ids
        ],
    }
    gdf_for_map = gdf_plot[gdf_plot["cluster"].notna()].copy()

    fig_map = px.choropleth_mapbox(
        gdf_for_map,
        geojson=geojson_clustered,
        locations="id",
        color="cluster_str",
        color_discrete_map={
            f"Cluster {c}: {df[df['cluster']==c]['cluster_label'].iloc[0]}": CLUSTER_COLORS[c]
            for c in CLUSTER_COLORS
        },
        mapbox_style="carto-positron",
        center={"lat": -2.5, "lon": 118},
        zoom=4,
        opacity=0.7,
        hover_name="nama_kab",
        hover_data={
            "nama_prop": True,
            "cluster_str": True,
            "populasi": ":.0f",
            "pdrb_perkapita_juta": ":.1f",
            "timbulan_per1k": ":.1f",
            "id": False,
        },
        labels={
            "cluster_str": "Cluster",
            "nama_prop": "Provinsi",
            "populasi": "Populasi",
            "pdrb_perkapita_juta": "PDRB/Kapita (Juta)",
            "timbulan_per1k": "Timbulan/1K",
        },
    )

    # Draw missing kabkota as grey dashed outlines (garis-garis)
    def geom_to_lines(geom):
        lats, lons = [], []
        if geom is None or geom.is_empty:
            return lats, lons
        polys = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
        for poly in polys:
            coords = list(poly.exterior.coords)
            lons += [c[0] for c in coords] + [None]
            lats += [c[1] for c in coords] + [None]
        return lats, lons

    miss_lats, miss_lons = [], []
    for geom in gdf_missing.geometry:
        lats, lons = geom_to_lines(geom)
        miss_lats.extend(lats)
        miss_lons.extend(lons)

    if miss_lats:
        fig_map.add_trace(go.Scattermapbox(
            lat=miss_lats,
            lon=miss_lons,
            mode="lines",
            line=dict(color="#999999", width=1, dash="dot") if hasattr(go.scattermapbox.Line, "dash") else dict(color="#999999", width=1),
            name="Tidak ada data",
            hoverinfo="skip",
            showlegend=True,
        ))

    fig_map.update_layout(height=580, margin=dict(t=0, b=0, l=0, r=0), legend_title="Cluster")
    st.plotly_chart(fig_map, use_container_width=True)

    matched = gdf_clustered.shape[0]
    st.caption(f"{matched}/{len(gdf_joined)} kabkota berhasil dipetakan ke shapefile.")


# ═══════════════════════════════════════════════════════════════════
# TAB 3 — PROFIL CLUSTER
# ═══════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Profil Fitur per Cluster")

    feature_group = st.radio(
        "Kelompok fitur:",
        ["Sumber Sampah", "Ekonomi", "Demografis", "Fasilitas & Timbulan", "Semua"],
        horizontal=True,
    )

    group_map = {
        "Sumber Sampah": SUMBER_PER1K,
        "Ekonomi": FEATURE_ECON,
        "Demografis": FEATURE_DEMOGRAFI,
        "Fasilitas & Timbulan": FEATURE_FAS + FEATURE_TIM,
        "Semua": ALL_FEATURES,
    }
    selected_features = group_map[feature_group]

    # Normalize per cluster (z-score across all kabkota) for radar
    cluster_means = dff.groupby(["cluster", "cluster_label"])[selected_features].mean().reset_index()

    col_radar, col_bar = st.columns([1, 1])

    with col_radar:
        st.markdown("**Radar Chart (nilai rata-rata per cluster)**")
        feat_labels = [FEATURE_LABELS.get(f, f) for f in selected_features]

        # Normalize 0-1 for radar
        mins = dff[selected_features].min()
        maxs = dff[selected_features].max()
        ranges = (maxs - mins).replace(0, 1)

        fig_radar = go.Figure()
        for _, row in cluster_means.iterrows():
            c = int(row["cluster"])
            vals = [(row[f] - mins[f]) / ranges[f] for f in selected_features]
            vals_closed = vals + [vals[0]]
            labels_closed = feat_labels + [feat_labels[0]]
            fig_radar.add_trace(go.Scatterpolar(
                r=vals_closed,
                theta=labels_closed,
                fill="toself",
                name=f"Cluster {c}: {row['cluster_label']}",
                line_color=CLUSTER_COLORS.get(c, "#999"),
                opacity=0.6,
            ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            height=420,
            margin=dict(t=20, b=20),
            legend=dict(orientation="v"),
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col_bar:
        st.markdown("**Bar Chart (nilai absolut rata-rata)**")
        feat_sel = st.selectbox("Pilih fitur:", options=selected_features,
                                format_func=lambda f: FEATURE_LABELS.get(f, f))
        fig_bar2 = px.bar(
            cluster_means.sort_values("cluster"),
            x="cluster_label", y=feat_sel,
            color="cluster",
            color_discrete_map=CLUSTER_COLORS,
            text_auto=".2f",
        )
        fig_bar2.update_layout(
            height=420, xaxis_title="", yaxis_title=FEATURE_LABELS.get(feat_sel, feat_sel),
            showlegend=False, margin=dict(t=20, b=20),
        )
        st.plotly_chart(fig_bar2, use_container_width=True)

    # Boxplot
    st.markdown("**Distribusi per Cluster**")
    feat_box = st.selectbox(
        "Pilih fitur untuk boxplot:",
        options=ALL_FEATURES,
        format_func=lambda f: FEATURE_LABELS.get(f, f),
        key="boxplot_feat",
    )
    fig_box = px.box(
        dff,
        x="cluster_label", y=feat_box,
        color="cluster",
        color_discrete_map=CLUSTER_COLORS,
        points="outliers",
        labels={"cluster_label": "Cluster", feat_box: FEATURE_LABELS.get(feat_box, feat_box)},
    )
    fig_box.update_layout(height=380, showlegend=False, margin=dict(t=20))
    st.plotly_chart(fig_box, use_container_width=True)

    # Top 10 members per cluster
    st.markdown("**Anggota Cluster (10 terbesar berdasarkan populasi)**")
    sel_c = st.selectbox(
        "Pilih cluster:",
        options=sorted(dff["cluster"].unique()),
        format_func=lambda c: f"Cluster {c}: {dff[dff['cluster']==c]['cluster_label'].iloc[0]}",
    )
    top10 = (
        dff[dff["cluster"] == sel_c]
        .sort_values("populasi", ascending=False)
        .head(10)[["kabkota", "provinsi", "ukuran_kota", "populasi",
                    "pdrb_perkapita_juta", "kepadatan", "timbulan_per1k",
                    "sampah_dikelola_per1k", "silhouette"]]
    )
    top10.columns = ["Kabkota", "Provinsi", "Ukuran", "Populasi",
                     "PDRB/Kapita (Juta)", "Kepadatan", "Timbulan/1K",
                     "Dikelola/1K", "Silhouette"]
    st.dataframe(top10, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 4 — CARI KABKOTA
# ═══════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Profil & Peer Kabupaten/Kota")

    search = st.selectbox(
        "Cari kabupaten/kota:",
        options=sorted(df["kabkota"].unique()),
    )

    row = df[df["kabkota"] == search].iloc[0]
    c = int(row["cluster"])

    # Header
    col_h1, col_h2, col_h3, col_h4 = st.columns(4)
    col_h1.metric("Cluster", f"Cluster {c}: {row['cluster_label']}")
    col_h2.metric("Ukuran Kota", row["ukuran_kota"].capitalize())
    col_h3.metric("Silhouette", f"{row['silhouette']:.4f}")
    col_h4.metric("Anomali", "Ya" if row["is_anomali"] else "Tidak")

    if row["is_anomali"]:
        st.warning(f"{search} terdeteksi sebagai anomali oleh Isolation Forest. Data perlu diverifikasi sebelum digunakan sebagai referensi.")

    # Quality score for this kabkota
    qs_row = dq[dq["kabkota"] == search]
    if not qs_row.empty:
        qs = qs_row.iloc[0]
        st.markdown("**Kualitas Data**")
        qc1, qc2, qc3, qc4 = st.columns(4)
        qc1.metric("Overall", f"{qs['qs_overall_10']:.2f} / 10")
        qc2.metric("Timbulan", f"{qs['qs_timbulan_10']:.2f} / 10")
        qc3.metric("Sumber Sampah", f"{qs['qs_sumber_10']:.2f} / 10")
        qc4.metric("Komposisi", f"{qs['qs_komposisi_10']:.2f} / 10")

    st.divider()
    col_info, col_peer = st.columns([1, 1])

    with col_info:
        st.markdown("**Profil Fitur**")
        # Compare this kabkota to cluster mean
        cluster_df = df[df["cluster"] == c]
        profile_rows = []
        for feat in ALL_FEATURES:
            val = row[feat]
            cmean = cluster_df[feat].mean()
            gmean = df[feat].mean()
            profile_rows.append({
                "Fitur": FEATURE_LABELS.get(feat, feat),
                "Nilai": round(val, 3),
                "Rata-rata Cluster": round(cmean, 3),
                "Rata-rata Nasional": round(gmean, 3),
            })
        prof_df = pd.DataFrame(profile_rows)
        st.dataframe(prof_df, use_container_width=True, hide_index=True)

    with col_peer:
        st.markdown("**5 Kabkota Paling Mirip**")

        DIMENSION_OPTIONS = {
            "Semua Dimensi": ALL_FEATURES,
            "Sumber Sampah": SUMBER_PER1K,
            "Ekonomi": FEATURE_ECON,
            "Demografis": FEATURE_DEMOGRAFI,
            "Fasilitas & Timbulan": FEATURE_FAS + FEATURE_TIM,
        }

        dim_sel = st.selectbox(
            "Dimensi kemiripan:",
            options=list(DIMENSION_OPTIONS.keys()),
            key="sim_dimension",
        )
        sim_feats = DIMENSION_OPTIONS[dim_sel]

        # Compute similarity dynamically using scaled Euclidean distance
        from sklearn.preprocessing import StandardScaler

        feat_df = df[["kabkota", "provinsi", "cluster", "cluster_label"] + sim_feats].dropna(subset=sim_feats)
        scaler = StandardScaler()
        X = scaler.fit_transform(feat_df[sim_feats].values)

        # Find index of selected kabkota in feat_df
        self_mask = feat_df["kabkota"] == search
        if self_mask.sum() == 0:
            st.warning("Data fitur tidak lengkap untuk kabkota ini pada dimensi yang dipilih.")
        else:
            self_idx = feat_df.index.get_loc(feat_df[self_mask].index[0])
            self_vec = X[self_idx]

            dists = np.linalg.norm(X - self_vec, axis=1)
            dists[self_idx] = np.inf  # exclude self

            d_max = np.percentile(dists[dists < np.inf], 95)
            scores = np.clip(100 * (1 - dists / d_max), 0, 100)

            top5_idx = np.argsort(dists)[:5]
            peers_dyn = []
            for rank, idx in enumerate(top5_idx, 1):
                pr = feat_df.iloc[idx]
                same_cluster = int(pr["cluster"]) == c
                peers_dyn.append({
                    "Rank": rank,
                    "Kabkota": pr["kabkota"],
                    "Provinsi": pr["provinsi"],
                    "Cluster": f"C{int(pr['cluster'])}: {pr['cluster_label']}",
                    "Similarity": f"{scores[idx]:.1f}%",
                    "Sama Cluster": "Ya" if same_cluster else "Tidak",
                })

            st.dataframe(pd.DataFrame(peers_dyn), use_container_width=True, hide_index=True)

            # Radar vs top 3 peers on selected features (up to 7 for readability)
            st.markdown("**Perbandingan dengan 3 Teratas**")
            st.caption(
                "Nilai dinormalisasi relatif terhadap 4 kota yang ditampilkan (0 = terendah, 1 = tertinggi di antara keempatnya). "
                "Gunakan tabel Profil Fitur di sebelah kiri untuk melihat nilai absolut."
            )
            radar_feats = sim_feats[:7] if len(sim_feats) > 7 else sim_feats
            r_labels = [FEATURE_LABELS.get(f, f) for f in radar_feats]

            # Normalize within the comparison group (selected + top 3 peers)
            # so differences between similar cities are visible
            compare_rows = [row] + [feat_df.iloc[idx] for idx in top5_idx[:3]]
            compare_df = pd.DataFrame([r[radar_feats] for r in compare_rows])
            mins_r = compare_df.min()
            maxs_r = compare_df.max()
            ranges_r = (maxs_r - mins_r).replace(0, 1)

            fig_r2 = go.Figure()
            vals_self = [(row[f] - mins_r[f]) / ranges_r[f] for f in radar_feats]
            vals_self_c = vals_self + [vals_self[0]]
            fig_r2.add_trace(go.Scatterpolar(
                r=vals_self_c,
                theta=r_labels + [r_labels[0]],
                fill="toself",
                name=search,
                line_color=CLUSTER_COLORS.get(c, "#333"),
                line_width=2,
            ))
            peer_colors = ["#3498db", "#e74c3c", "#f39c12"]
            for rank, idx in enumerate(top5_idx[:3], 1):
                pr = feat_df.iloc[idx]
                vals_p = [(pr[f] - mins_r[f]) / ranges_r[f] for f in radar_feats]
                fig_r2.add_trace(go.Scatterpolar(
                    r=vals_p + [vals_p[0]],
                    theta=r_labels + [r_labels[0]],
                    fill="toself",
                    fillcolor=peer_colors[rank - 1],
                    name=pr["kabkota"],
                    opacity=0.35,
                    line=dict(color=peer_colors[rank - 1], width=1.5),
                ))
            fig_r2.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                height=360,
                margin=dict(t=10, b=10),
            )
            st.plotly_chart(fig_r2, use_container_width=True)

    # Full data row
    with st.expander("Lihat semua data"):
        st.dataframe(pd.DataFrame([row]), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 5 — KUALITAS DATA
# ═══════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("Kualitas Data SIPSN 2024")
    st.caption(
        "Skor kualitas dihitung dari 3 komponen: Report Rate (partisipasi pelaporan), "
        "Completeness (kelengkapan isian), dan Outlier Quality (konsistensi nilai). "
        "Skala 0–10."
    )

    # Filter quality data to match sidebar filters
    dq_filt = dq[
        dq["cluster"].isin(selected_clusters) &
        dq["provinsi"].isin(selected_provinsi) &
        dq["ukuran_kota"].isin(selected_ukuran)
    ].copy()

    # ── Metric row ────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rata-rata Skor Overall", f"{dq_filt['qs_overall_10'].mean():.2f} / 10")
    c2.metric("Rata-rata Skor Timbulan", f"{dq_filt['qs_timbulan_10'].mean():.2f} / 10")
    c3.metric("Rata-rata Skor Sumber", f"{dq_filt['qs_sumber_10'].mean():.2f} / 10")
    c4.metric("Rata-rata Skor Komposisi", f"{dq_filt['qs_komposisi_10'].mean():.2f} / 10")

    st.divider()

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("**Distribusi Skor Overall per Cluster**")
        fig_qs_box = px.box(
            dq_filt,
            x="cluster_label", y="qs_overall_10",
            color="cluster",
            color_discrete_map=CLUSTER_COLORS,
            points="outliers",
            labels={"cluster_label": "Cluster", "qs_overall_10": "Skor Kualitas (0-10)"},
        )
        fig_qs_box.update_layout(height=360, showlegend=False, margin=dict(t=10, b=10))
        st.plotly_chart(fig_qs_box, use_container_width=True)

    with col_right:
        st.markdown("**Komponen Kualitas rata-rata per Provinsi**")
        prov_qs = dq_filt.groupby("provinsi")[
            ["qs_timbulan_10", "qs_sumber_10", "qs_komposisi_10"]
        ].mean().round(2).reset_index()
        prov_qs = prov_qs.sort_values("qs_timbulan_10")
        fig_prov = px.bar(
            prov_qs.melt(id_vars="provinsi",
                         value_vars=["qs_timbulan_10", "qs_sumber_10", "qs_komposisi_10"],
                         var_name="Komponen", value_name="Skor"),
            x="Skor", y="provinsi", color="Komponen",
            barmode="group",
            color_discrete_map={
                "qs_timbulan_10": "#3498db",
                "qs_sumber_10": "#2ecc71",
                "qs_komposisi_10": "#f39c12",
            },
            labels={
                "qs_timbulan_10": "Timbulan",
                "qs_sumber_10": "Sumber",
                "qs_komposisi_10": "Komposisi",
                "provinsi": "",
            },
        )
        fig_prov.update_layout(height=max(360, len(prov_qs) * 20), margin=dict(t=10, b=10))
        st.plotly_chart(fig_prov, use_container_width=True)

    # ── Heatmap komponen per kabkota ──────────────────────────────
    st.markdown("**Heatmap Komponen Kualitas per Kabkota**")
    st.caption("Warna merah = skor rendah, hijau = skor tinggi.")

    hm_df = dq_filt.sort_values("qs_overall_10")[
        ["kabkota", "provinsi", "report_rate", "sumber_completeness",
         "komp_completeness", "outlier_quality", "qs_overall_10"]
    ].copy()
    hm_df.columns = ["Kabkota", "Provinsi", "Report Rate", "Completeness Sumber",
                     "Completeness Komposisi", "Outlier Quality", "Skor Overall"]
    for col in ["Report Rate", "Completeness Sumber", "Completeness Komposisi", "Outlier Quality"]:
        hm_df[col] = (hm_df[col] * 10).round(2)

    st.dataframe(
        hm_df.style.background_gradient(
            subset=["Report Rate", "Completeness Sumber", "Completeness Komposisi",
                    "Outlier Quality", "Skor Overall"],
            cmap="RdYlGn", vmin=0, vmax=10
        ),
        use_container_width=True,
        hide_index=True,
        height=400,
    )

    # ── Kabkota dengan skor rendah ────────────────────────────────
    st.markdown("**Kabkota dengan Kualitas Data Terendah (Bottom 20)**")
    bottom20 = dq_filt.nsmallest(20, "qs_overall_10")[
        ["kabkota", "provinsi", "cluster_label",
         "qs_timbulan_10", "qs_sumber_10", "qs_komposisi_10", "qs_overall_10"]
    ].copy()
    bottom20.columns = ["Kabkota", "Provinsi", "Cluster",
                        "Timbulan", "Sumber", "Komposisi", "Overall"]
    st.dataframe(bottom20, use_container_width=True, hide_index=True)

    st.download_button(
        label="Download Quality Score (CSV)",
        data=dq_filt.to_csv(index=False).encode("utf-8"),
        file_name="quality_score_filtered.csv",
        mime="text/csv",
    )
