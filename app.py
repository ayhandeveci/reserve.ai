
import json
import os
import streamlit as st
import pandas as pd

from core.io import load_input_data, normalize_triangle_like
from core.guards import section_toggle, secure_delete
from core.stats import run_basic_eda
from core.export import export_tur1_excel, build_tur1_summary
from core.prompts import prompt_tur1, prompt_tur2_from_excel, prompt_tur3
from core.schemas import validate_json_output
from core.viz import render_visuals
from services.llm_client import call_llm

st.set_page_config(page_title="reserveai — Kasko Hasar Analizi", layout="wide")

st.title("reserveai · Kasko — 3 Turlu Akış")
st.caption("Tur-1: EDA → Tur-2: Öneriler → Tur-3: Görselleştirme")

with st.sidebar:
    st.markdown("### Genel Ayarlar")
    st.info("Her section kendi API anahtarını alır; section kapandığında anahtar **silinecektir**.")
    st.divider()
    st.markdown("**Örnek veri** için: `assets/kasko_cumulative_claims_sample.csv`")

# --- Tur-1 (Analiz/EDA) ---
st.header("Tur 1 — Analiz (Kümülatif Gerçekleşen)")
active_1 = section_toggle("tur1_active", label="Tur 1 Aktif mi?")
if active_1:
    col1, col2 = st.columns([2,1])
    with col1:
        src = st.radio("Veri kaynağı", ["CSV yükle", "Örnek veriyi kullan"], horizontal=True, key="tur1_src")
        if src == "CSV yükle":
            up = st.file_uploader("Kümülatif gerçekleşen hasar verisini yükle (CSV)", type=["csv"], key="tur1_file")
            df = load_input_data(up) if up else None
        else:
            df = load_input_data("assets/kasko_cumulative_claims_sample.csv")

        if df is not None:
            st.success(f"Veri yüklendi: {len(df):,} satır")
            with st.expander("İlk satırlar", expanded=False):
                st.dataframe(df.head(50), use_container_width=True)
            df_norm, notes_norm = normalize_triangle_like(df)
            if notes_norm:
                st.warning("\n".join(notes_norm))
            st.session_state["tur1_df_norm"] = df_norm
        else:
            st.stop()

    with col2:
        api_key = st.text_input("OpenAI API Key (Tur 1)", type="password", key="tur1_api")
        model = st.text_input("Model (örn: gpt-5.1-mini, gpt-4.1)", value="gpt-5.1-mini", key="tur1_model")
        run_btn = st.button("Tur 1 — Analiz başlat", use_container_width=True)

    if run_btn:
        with st.spinner("Tur-1: EDA çalışıyor..."):
            eda_result = run_basic_eda(st.session_state["tur1_df_norm"])
            # GPT'ye kısa bir özetletme (opsiyonel); ana çıktı yine de EDA sözlüğü
            prompt = prompt_tur1(eda_result)
            llm_summary = None
            if api_key:
                llm_summary = call_llm(api_key, model, prompt)
            payload = {"eda": eda_result, "llm_summary": llm_summary}
            st.session_state["tur1_out"] = payload
            st.success("Tur-1 tamamlandı ve çıktı kaydedildi.")
            with st.expander("Tur-1 Çıktısı (JSON)", expanded=False):
                st.json(payload)

else:
    # Section kapandı -> ilgili bilgileri sil
    secure_delete(["tur1_api", "tur1_out", "tur1_df_norm", "tur1_file"])

st.divider()

# --- Tur-2 (Öneriler) ---
st.header("Tur 2 — Öneriler (Detaylara inme)")
active_2 = section_toggle("tur2_active", label="Tur 2 Aktif mi?")
if active_2:
    if "tur1_out" not in st.session_state or "tur1_df_norm" not in st.session_state:
        st.warning("Tur-2 için Tur-1 verisi ve çıktısı gerekli.")
        st.stop()

    col1, col2 = st.columns([2,1])
    with col1:
        st.write("Tur-1 EDA özetine ve **orijinal normalize veri**ye bakarak veri kalitesi, segmentasyon ve ek alan/özellik önerilerini üret.")
        with st.expander("Tur-1 EDA Özeti", expanded=False):
            st.json(st.session_state["tur1_out"]["eda"])

    with col2:
        api_key2 = st.text_input("OpenAI API Key (Tur 2)", type="password", key="tur2_api")
        model2 = st.text_input("Model", value=st.session_state.get("tur1_model","gpt-5.1-mini"), key="tur2_model")
        run2 = st.button("Tur 2 — Önerileri üret", use_container_width=True)

    if run2:
        with st.spinner("Tur-2: Öneriler hazırlanıyor..."):
            df_norm = st.session_state["tur1_df_norm"]
            excel_sum = tur1_excel_summary if tur1_excel_summary is not None else {"note": "excel not uploaded"}
                prompt2 = prompt_tur2_from_excel(excel_sum, st.session_state["tur1_out"]["eda"])
            suggestions = None
            if api_key2:
                suggestions = call_llm(api_key2, model2, prompt2)
            # Eğer LLM kullanılmadıysa bile boş bir iskelet döndür
            if not suggestions:
                suggestions = {"notes": "LLM çağrısı yapılmadı; demo iskeleti.", "segments": [], "features": []}
            # JSON doğrulama (yumuşak)
            suggestions = validate_json_output(suggestions, expected_keys=["methods","thresholds","workflow","notes"])
            st.session_state["tur2_out"] = suggestions
            st.success("Tur-2 tamamlandı ve çıktı kaydedildi.")
            with st.expander("Tur-2 Çıktısı (JSON)", expanded=False):
                st.json(suggestions)
else:
    secure_delete(["tur2_api", "tur2_out"])

st.divider()

# --- Tur-3 (Görselleştirme) ---
st.header("Tur 3 — Görselleştirme")
active_3 = section_toggle("tur3_active", label="Tur 3 Aktif mi?")
if active_3:
    if ("tur1_df_norm" not in st.session_state) or ("tur1_out" not in st.session_state) or ("tur2_out" not in st.session_state):
        st.warning("Tur-3 için Tur-1 verisi/çıktısı ve Tur-2 çıktısı gerekli.")
        st.stop()

    col1, col2 = st.columns([2,1])
    with col1:
        st.write("Tur-1 & Tur-2 çıktıları ve normalize veri ile grafik üret.")
        with st.expander("Tur-1 & Tur-2 özetleri", expanded=False):
            st.json({"tur1": st.session_state["tur1_out"], "tur2": st.session_state["tur2_out"]})
    with col2:
        api_key3 = st.text_input("OpenAI API Key (Tur 3)", type="password", key="tur3_api")
        model3 = st.text_input("Model", value=st.session_state.get("tur2_model","gpt-5.1-mini"), key="tur3_model")
        run3 = st.button("Tur 3 — Görselleştir", use_container_width=True)

    if run3:
        with st.spinner("Tur-3: Grafikler oluşturuluyor..."):
            df_norm = st.session_state["tur1_df_norm"]
            prompt3 = prompt_tur3(df_norm, st.session_state["tur1_out"], st.session_state["tur2_out"])
            viz_spec = None
            if api_key3:
                viz_spec = call_llm(api_key3, model3, prompt3)
            # LLM grafikleri tanımlamazsa, yerel varsayılanları çiz
            render_visuals(df_norm, st.session_state["tur1_out"], st.session_state["tur2_out"], viz_spec)
            st.success("Tur-3 görselleştirme tamamlandı.")
else:
    secure_delete(["tur3_api"])
