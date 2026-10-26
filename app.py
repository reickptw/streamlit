# -*- coding: utf-8 -*-
"""
Dashboard Interaktif Pertumbuhan Tunas Pohon di bawah Perlakuan Zat Pengatur Tumbuh
Tugas Python Streamlit - Dataset: Kaggle (cjs.csv)
Jalankan:  streamlit run app.py
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Dashboard Pertumbuhan Tunas", page_icon="🌳", layout="wide")

DATA_PATH = Path(__file__).parent / "cjs.csv"


# ------------------------------------------------------------------
# 1. LOAD & CLEANING DATA
# ------------------------------------------------------------------
@st.cache_data
def load_data() -> pd.DataFrame:
    # Tanda "?" = ruas tidak ada (kolom INTERNODE) atau cabang tidak diketahui (kolom BR) -> NaN
    df = pd.read_csv(DATA_PATH, na_values="?")
    df = df.rename(columns={"TR": "Perlakuan", "TREE": "Pohon", "BR": "Cabang",
                            "TL": "Panjang_Tunas", "IN": "Jumlah_Ruas"})
    # 12 baris punya cabang "?" -> beri label agar tidak NaN (NaN merusak filter/sorting)
    df["Cabang"] = df["Cabang"].fillna("Tidak diketahui")
    ruas_cols = [c for c in df.columns if c.startswith("INTERNODE_")]
    df[ruas_cols] = df[ruas_cols].apply(pd.to_numeric, errors="coerce")
    # Fitur turunan: rata-rata panjang ruas per tunas
    df["Rata_Panjang_Ruas"] = df[ruas_cols].mean(axis=1)
    return df


df = load_data()
RUAS_COLS = [c for c in df.columns if c.startswith("INTERNODE_")]

# ------------------------------------------------------------------
# 2. JUDUL & DESKRIPSI
# ------------------------------------------------------------------
st.title("🌳 Dashboard Pertumbuhan Tunas Pohon")
st.markdown(
    """
Dashboard ini menganalisis **pertumbuhan tunas (shoot) pohon** pada beberapa perlakuan
zat pengatur tumbuh (*PP-333* dan *EL-500* pada dua konsentrasi, serta kontrol).
Setiap baris adalah satu tunas dengan **panjang total (TL)**, **jumlah ruas (IN)**, dan
**panjang tiap ruas** (INTERNODE_1 s.d. INTERNODE_29). Gunakan filter di sidebar untuk menjelajahi data.
"""
)

# ------------------------------------------------------------------
# 3. FILTER INTERAKTIF (sidebar) - 4 filter
# ------------------------------------------------------------------
st.sidebar.header("🔎 Filter Data")

perlakuan_opsi = sorted(df["Perlakuan"].unique())
f_perlakuan = st.sidebar.multiselect("Perlakuan", perlakuan_opsi, default=perlakuan_opsi)

cabang_opsi = sorted(df["Cabang"].unique())
f_cabang = st.sidebar.multiselect("Cabang (BR)", cabang_opsi, default=cabang_opsi)

tl_min, tl_max = float(df["Panjang_Tunas"].min()), float(df["Panjang_Tunas"].max())
f_tl = st.sidebar.slider("Panjang tunas (TL)", tl_min, tl_max, (tl_min, tl_max))

in_min, in_max = int(df["Jumlah_Ruas"].min()), int(df["Jumlah_Ruas"].max())
f_in = st.sidebar.slider("Jumlah ruas (IN)", in_min, in_max, (in_min, in_max))

data = df[
    df["Perlakuan"].isin(f_perlakuan)
    & df["Cabang"].isin(f_cabang)
    & df["Panjang_Tunas"].between(*f_tl)
    & df["Jumlah_Ruas"].between(*f_in)
]

st.sidebar.caption(f"Data terpilih: **{len(data):,}** dari {len(df):,} baris")

if data.empty:
    st.warning("Tidak ada data yang cocok dengan filter. Ubah pilihan filter di sidebar.")
    st.stop()

# ------------------------------------------------------------------
# 4. KPI - 5 indikator
# ------------------------------------------------------------------
st.subheader("📌 Indikator Utama (KPI)")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Tunas Diamati", f"{len(data):,}")
k2.metric("Rata-rata Panjang Tunas", f"{data['Panjang_Tunas'].mean():.2f}")
k3.metric("Rata-rata Jumlah Ruas", f"{data['Jumlah_Ruas'].mean():.2f}")
k4.metric("Rata-rata Panjang Ruas", f"{data['Rata_Panjang_Ruas'].mean():.2f}")
k5.metric("Jumlah Pohon", f"{data['Pohon'].nunique()}")

st.divider()

# ------------------------------------------------------------------
# 5. VISUALISASI - 6 jenis chart
# ------------------------------------------------------------------
# (1) Bar chart + (2) Pie chart
c1, c2 = st.columns(2)

with c1:
    st.markdown("**1. Bar Chart - Rata-rata Panjang Tunas per Perlakuan**")
    bar_df = data.groupby("Perlakuan", as_index=False)["Panjang_Tunas"].mean()
    bar_df = bar_df.sort_values("Panjang_Tunas", ascending=False)
    fig = px.bar(bar_df, x="Perlakuan", y="Panjang_Tunas", color="Perlakuan",
                 text_auto=".2f", labels={"Panjang_Tunas": "Rata-rata panjang tunas"})
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.markdown("**2. Pie Chart - Proporsi Jumlah Tunas per Perlakuan**")
    pie_df = data["Perlakuan"].value_counts().reset_index()
    pie_df.columns = ["Perlakuan", "Jumlah"]
    fig = px.pie(pie_df, names="Perlakuan", values="Jumlah", hole=0.35)
    st.plotly_chart(fig, use_container_width=True)

# (3) Histogram + (4) Scatter plot
c3, c4 = st.columns(2)

with c3:
    st.markdown("**3. Histogram - Distribusi Panjang Tunas**")
    batas = st.slider("Batas atas sumbu panjang tunas (agar histogram terbaca)",
                      10, int(tl_max), 60, key="batas_hist")
    hist_df = data[data["Panjang_Tunas"] <= batas]
    fig = px.histogram(hist_df, x="Panjang_Tunas", color="Perlakuan", nbins=40,
                       barmode="overlay", opacity=0.65,
                       labels={"Panjang_Tunas": "Panjang tunas"})
    st.plotly_chart(fig, use_container_width=True)

with c4:
    st.markdown("**4. Scatter Plot - Jumlah Ruas vs Panjang Tunas**")
    fig = px.scatter(data, x="Jumlah_Ruas", y="Panjang_Tunas", color="Perlakuan",
                     opacity=0.6, hover_data=["Pohon", "Cabang"],
                     labels={"Jumlah_Ruas": "Jumlah ruas", "Panjang_Tunas": "Panjang tunas"})
    st.plotly_chart(fig, use_container_width=True)

# (5) Line chart + (6) Heatmap
c5, c6 = st.columns(2)

with c5:
    st.markdown("**5. Line Chart - Rata-rata Panjang Ruas menurut Posisi Ruas**")
    long_df = data.melt(id_vars="Perlakuan", value_vars=RUAS_COLS,
                        var_name="Posisi", value_name="Panjang_Ruas").dropna()
    long_df["Posisi"] = long_df["Posisi"].str.replace("INTERNODE_", "", regex=False).astype(int)
    line_df = long_df.groupby(["Perlakuan", "Posisi"]).agg(
        Rata_Ruas=("Panjang_Ruas", "mean"), n=("Panjang_Ruas", "size")).reset_index()
    line_df = line_df[line_df["n"] >= 20]  # hindari titik dengan sampel terlalu sedikit
    fig = px.line(line_df, x="Posisi", y="Rata_Ruas", color="Perlakuan", markers=True,
                  labels={"Posisi": "Posisi ruas (dari pangkal)", "Rata_Ruas": "Rata-rata panjang ruas"})
    st.plotly_chart(fig, use_container_width=True)

with c6:
    st.markdown("**6. Heatmap - Rata-rata Panjang Tunas (Perlakuan × Cabang)**")
    heat = data.pivot_table(index="Perlakuan", columns="Cabang",
                            values="Panjang_Tunas", aggfunc="mean")
    fig = px.imshow(heat, text_auto=".1f", aspect="auto", color_continuous_scale="YlGn",
                    labels={"color": "Rata-rata TL", "x": "Cabang", "y": "Perlakuan"})
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------------
# 6. TABEL DATA & UNDUH
# ------------------------------------------------------------------
with st.expander("📄 Lihat data hasil filter"):
    tampil = ["Perlakuan", "Pohon", "Cabang", "Panjang_Tunas", "Jumlah_Ruas", "Rata_Panjang_Ruas"]
    st.dataframe(data[tampil], use_container_width=True)
    st.download_button("⬇️ Unduh data terfilter (CSV)",
                       data[tampil].to_csv(index=False).encode("utf-8"),
                       file_name="data_terfilter.csv", mime="text/csv")

st.caption("Sumber data: Kaggle (cjs.csv) • Dibuat dengan Python, Streamlit & Plotly")
