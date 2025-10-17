
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

def render_visuals(df_norm: pd.DataFrame, tur1_out, tur2_out, viz_spec=None):
    st.subheader("Incurred — AY Gelişim Eğrileri")
    curve = alt.Chart(df_norm).mark_line().encode(
        x=alt.X("development_quarter:O", title="Gelişim Çeyreği"),
        y=alt.Y("incurred_cum:Q", title="Kümülatif Incurred"),
        color=alt.Color("accident_year:N", title="AY")
    ).properties(height=300)
    st.altair_chart(curve, use_container_width=True)

    if {"paid_cum","incurred_cum","development_quarter"}.issubset(df_norm.columns):
        st.subheader("Paid / Incurred Oranı — Gelişim Çeyreği")
        tmp = df_norm.groupby("development_quarter", as_index=False).agg(
            paid=("paid_cum","sum"),
            incurred=("incurred_cum","sum")
        )
        tmp["ratio"] = tmp["paid"] / tmp["incurred"]
        bar = alt.Chart(tmp).mark_bar().encode(
            x="development_quarter:O", y="ratio:Q"
        ).properties(height=250)
        st.altair_chart(bar, use_container_width=True)

    # Heatmap: incremental incurred by AY vs DevQ
    try:
        st.subheader("Incremental Incurred — Heatmap")
        df_sorted = df_norm.sort_values(["accident_year","development_quarter"])
        df_sorted["inc_incr"] = df_sorted.groupby("accident_year")["incurred_cum"].diff().fillna(df_sorted["incurred_cum"])
        heat = alt.Chart(df_sorted).mark_rect().encode(
            x=alt.X("development_quarter:O", title="DevQ"),
            y=alt.Y("accident_year:O", title="AY"),
            color=alt.Color("inc_incr:Q", title="Incremental Incurred", scale=alt.Scale(scheme="blues"))
        ).properties(height=250)
        st.altair_chart(heat, use_container_width=True)
    except Exception:
        pass

def apply_iqr_on_ata(df_norm: pd.DataFrame):
    # Build age-to-age factors at aggregated level; flag outliers using Tukey fences
    piv = df_norm.pivot_table(index="accident_year", columns="development_quarter", values="incurred_cum", aggfunc="last")
    ata_rows = []
    for j in range(1, piv.shape[1]):
        prev_col, next_col = j, j+1
        if (prev_col in piv.columns) and (next_col in piv.columns):
            ratios = (piv[next_col] / piv[prev_col]).dropna()
            if ratios.empty: 
                continue
            q1, q3 = ratios.quantile([0.25, 0.75])
            iqr = q3 - q1
            lo, hi = q1 - 1.5*iqr, q3 + 1.5*iqr
            for ay, r in ratios.items():
                ata_rows.append({"age": f"{j}->{j+1}", "accident_year": int(ay), "factor": float(r), "is_outlier": bool(r<lo or r>hi), "lo": float(lo), "hi": float(hi)})
    return pd.DataFrame(ata_rows)

def render_outlier_result(df_flags: pd.DataFrame):
    if df_flags.empty:
        st.info("Outlier bulunamadı (IQR/Tukey).")
        return
    st.subheader("Age-to-Age Faktörlerinde IQR Outlierları")
    st.dataframe(df_flags, use_container_width=True)
    chart = alt.Chart(df_flags).mark_circle(size=90).encode(
        x="age:N",
        y="factor:Q",
        color=alt.Color("is_outlier:N", title="Outlier?"),
        tooltip=["accident_year","factor","lo","hi"]
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)
