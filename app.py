# app.py — reserveai (Kasko) • 3 Turlu Akış
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

# ────────────────────────────────────────────────────────────────────────────────
# Sidebar
with st.sidebar:
    st.markdown("### Genel Ayarlar")
    st.info("Her section kendi API anahtarını alır; section kapandığında anahtar **silinecektir**.")
    st.divider()
    st.markdown("**Örnek veri** için: `assets/kasko_cumulative_claims_sample.csv`")

# ────────────────────────────────────────────────────────────────────────────────
# Tur-1 (Analiz/EDA)
st.header("Tur 1 — Analiz (Kümülatif Gerçekleşen)")
active_1 = section_toggle("tur1_active", label="Tur 1 Aktif mi?")
if active_1:
    col1, col2 = st.columns([2, 1])
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
        model = st.text_input("Model (örn: gpt-4o-mini, gpt-4.1)", value="gpt-4o-mini", key="tur1_model")
        run_btn = st.button("Tur 1 — Analiz başlat", use_container_width=True)

    if run_btn:
        with st.spinner("Tur-1: EDA çalışıyor..."):
            df_norm = st.session_state["tur1_df_norm"]
            eda_result = run_basic_eda(df_norm)

            # GPT'ye kısa özet (opsiyonel)
            llm_summary = None
            try:
                prompt = prompt_tur1(eda_result)
                if api_key:
                    llm_summary = call_llm(api_key, model, prompt)
            except Exception:
                llm_summary = None

            payload = {"eda": eda_result, "llm_summary": llm_summary}
            st.session_state["tur1_out"] = payload

            # EXCEL RAPORU OLUŞTUR & İNDİR
            xls = export_tur1_excel(df_norm, build_tur1_summary(df_norm))
            st.session_state["tur1_excel_bytes"] = xls.getvalue()
            st.success("Tur-1 tamamlandı. Excel raporu hazır.")
            st.download_button(
                "Tur-1 Excel Raporunu İndir",
                data=xls.getvalue(),
                file_name="reserveai_tur1_summary.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            with st.expander("Tur-1 Çıktısı (JSON)", expanded=False):
                st.json(payload)

else:
    # Section kapandı -> ilgili bilgileri sil
    secure_delete(["tur1_api", "tur1_out", "tur1_df_norm", "tur1_file", "tur1_excel_bytes"])

st.divider()

# ────────────────────────────────────────────────────────────────────────────────
# Tur-2 (Öneriler)
st.header("Tur 2 — Öneriler (Detaylara inme)")
active_2 = section_toggle("tur2_active", label="Tur 2 Aktif mi?")
if active_2:
    if "tur1_out" not in st.session_state or "tur1_df_norm" not in st.session_state:
        st.warning("Tur-2 için Tur-1 verisi ve çıktısı gerekli.")
        st.stop()

    col1, col2 = st.columns([2, 1])
    with col1:
        st.write("Tur-1 Excel özetini yükle ve orijinal normalize veri ile **outlier analiz planı** oluştur.")
        # Tur-1 Excel geri yükleme
        tur1_excel_summary = None
        up_xls = st.file_uploader("Tur-1 Excel (reserveai_tur1_summary.xlsx)", type=["xlsx"], key="tur2_xls")
        if up_xls is not None:
            try:
                x = pd.read_excel(up_xls, sheet_name=None)
                shape = x.get("Summary")
                cols = x.get("Columns")
                sums = x.get("NumericSums")
                segs = x.get("Segments")
                ata = x.get("AgeToAge")
                tur1_excel_summary = {
                    "shape": shape.to_dict(orient="records")[0] if shape is not None and len(shape) else {},
                    "columns": cols.to_dict(orient="records") if cols is not None else [],
                    "numeric_sums": sums.to_dict(orient="records") if sums is not None else [],
                    "segments": segs.to_dict(orient="records") if segs is not None else [],
                    "age_to_age": ata.to_dict(orient="records") if ata is not None else [],
                }
            except Exception as e:
                st.error(f"Excel okuma hatası: {e}")

        with st.expander("Tur-1 EDA Özeti", expanded=False):
            st.json(st.session_state["tur1_out"]["eda"])

    with col2:
        api_key2 = st.text_input("OpenAI API Key (Tur 2)", type="password", key="tur2_api")
        model2 = st.text_input("Model", value=st.session_state.get("tur1_model", "gpt-4o-mini"), key="tur2_model")
        run2 = st.button("Tur 2 — Önerileri üret", use_container_width=True)

    if run2:
        with st.spinner("Tur-2: Öneriler hazırlanıyor..."):
            df_norm = st.session_state["tur1_df_norm"]
            excel_sum = tur1_excel_summary if tur1_excel_summary is not None else {"note": "excel not uploaded"}
            prompt2 = prompt_tur2_from_excel(excel_sum, st.session_state["tur1_out"]["eda"])

            suggestions = None
            if api_key2:
                suggestions = call_llm(api_key2, model2, prompt2)

            # Eğer LLM çağrısı yoksa demo iskeleti
            if not suggestions or not isinstance(suggestions, dict):
                suggestions = {
                    "top_recommendation": {
                        "method": "IQR (age-to-age)",
                        "why": "Basit ve güçlü: faktörlerdeki sıra dışı değerleri hızlıca işaretler.",
                        "when_to_use": "AY-DevQ faktörleri makul sayıda AY içeriyorsa",
                        "parameters": [{"name": "fence", "hint": "1.5×IQR (Tukey)"}],
                    },
                    "alternatives": [
                        {"method": "z-score (incremental)", "why": "Çeyreğe göre normalize edilen artışlar"},
                        {"method": "MAD/robust z", "why": "Aykırıya dayanıklı"},
                    ],
                    "workflow": [
                        "Age-to-age faktörlerini üret",
                        "IQR ile alt/üst sınırları hesapla",
                        "Taşanları işaretle ve gözden geçir",
                    ],
                    "notes": "LLM çağrısı yapılmadı; demo iskeleti.",
                }

            # JSON doğrulama (yumuşak)
            suggestions = validate_json_output(
                suggestions, expected_keys=["methods", "thresholds", "workflow", "notes"]
            )
            st.session_state["tur2_out"] = suggestions

            # Önerilen yöntemi ekrana yaz + seçtirme
            top = None
            try:
                top = suggestions.get("top_recommendation", None)
            except Exception:
                top = None

            if top and isinstance(top, dict) and top.get("method"):
                st.success(f"Önerilen yöntem: **{top.get('method')}** — {top.get('why','')}")
                methods = [top.get("method")] + [
                    a.get("method")
                    for a in suggestions.get("alternatives", [])
                    if isinstance(a, dict) and a.get("method")
                ]
                methods = [m for m in methods if m]
                chosen = st.selectbox("Uygulanacak yöntem:", methods, index=0, key="method_choice_select")
                st.session_state["method_choice"] = chosen
            else:
                st.info("Öneri bulunamadı; varsayılan yöntem: IQR (age-to-age).")
                st.session_state["method_choice"] = "IQR (age-to-age)"

            st.success("Tur-2 tamamlandı ve çıktı kaydedildi.")
            with st.expander("Tur-2 Çıktısı (JSON)", expanded=False):
                st.json(suggestions)

            if "method_choice" in st.session_state:
                st.caption(f"Seçili yöntem: **{st.session_state['method_choice']}**")
else:
    secure_delete(["tur2_api", "tur2_out", "method_choice"])

st.divider()

# ────────────────────────────────────────────────────────────────────────────────
# Tur-3 (Görselleştirme + Uygulama + Anlatım)
st.header("Tur 3 — Görselleştirme")
active_3 = section_toggle("tur3_active", label="Tur 3 Aktif mi?")
if active_3:
    if ("tur1_df_norm" not in st.session_state) or ("tur1_out" not in st.session_state) or ("tur2_out" not in st.session_state):
        st.warning("Tur-3 için Tur-1 verisi/çıktısı ve Tur-2 çıktısı gerekli.")
        st.stop()

    col1, col2 = st.columns([2, 1])
    with col1:
        st.write("Tur-1 & Tur-2 çıktıları ve normalize veri ile grafik + seçilen yöntem analizi.")
        with st.expander("Tur-1 & Tur-2 özetleri", expanded=False):
            st.json({"tur1": st.session_state["tur1_out"], "tur2": st.session_state["tur2_out"]})
    with col2:
        api_key3 = st.text_input("OpenAI API Key (Tur 3)", type="password", key="tur3_api")
        model3 = st.text_input("Model", value=st.session_state.get("tur2_model", "gpt-4o-mini"), key="tur3_model")
        run3 = st.button("Tur 3 — Görselleştir", use_container_width=True)

    if run3:
        with st.spinner("Tur-3: Grafikler oluşturuluyor ve yöntem uygulanıyor..."):
            df_norm = st.session_state["tur1_df_norm"]
            viz_spec = None

            # 1) LLM'den kısa anlatım (opsiyonel)
            narr = None
            try:
                prompt3 = prompt_tur3(df_norm, st.session_state["tur1_out"], st.session_state["tur2_out"])
                if api_key3:
                    narr = call_llm(api_key3, model3, prompt3)
            except Exception:
                narr = None

            if isinstance(narr, dict):
                st.subheader("Seçilen Yöntem — Kısa Anlatım (LLM)")
                if narr.get("chosen_method"):
                    st.write(f"**Yöntem:** {narr['chosen_method']}")
                if narr.get("reason"):
                    st.write(f"**Neden:** {narr['reason']}")
                if narr.get("narrative"):
                    st.write(narr["narrative"])

            # 2) Kullanıcı/LLM seçimini belirle
            chosen = st.session_state.get("method_choice", None)
            if not chosen and isinstance(narr, dict) and narr.get("chosen_method"):
                chosen = narr["chosen_method"]
            if not chosen and isinstance(st.session_state.get("tur2_out"), dict):
                tr = st.session_state["tur2_out"].get("top_recommendation", {})
                chosen = tr.get("method")
            if not chosen:
                chosen = "IQR (age-to-age)"  # güvenli varsayılan

            st.markdown(f"### Uygulanan Yöntem: **{chosen}**")
            st.markdown("Aşağıda yöntemin uygulanması, grafikler ve kısa yorum yer alır.")

            # 3) Yönteme göre uygulama
            low = chosen.lower()
            if "iqr" in low and "age" in low:
                from core.viz import apply_iqr_on_ata, render_outlier_result_iqr
                flags = apply_iqr_on_ata(df_norm)
                render_visuals(df_norm, st.session_state["tur1_out"], st.session_state["tur2_out"], viz_spec)
                render_outlier_result_iqr(flags)
                st.success("IQR (Tukey) ile age-to-age faktörlerinde olası uç değerler işaretlendi.")
            elif "z" in low and "score" in low:
                from core.viz import apply_zscore_on_incremental, render_outlier_result_zscore
                ztab = apply_zscore_on_incremental(df_norm, col="incurred_cum", z=3.0)
                render_visuals(df_norm, st.session_state["tur1_out"], st.session_state["tur2_out"], viz_spec)
                render_outlier_result_zscore(ztab, z=3.0)
                st.success("z-score (|z|≥3) ile incremental incurred outlier analizi yapıldı.")
            else:
                # Diğer yöntemler için şimdilik genel görseller + açıklama
                render_visuals(df_norm, st.session_state["tur1_out"], st.session_state["tur2_out"], viz_spec)
                st.info("Seçilen yöntemin özel uygulaması henüz kodlanmadı. Genel grafikler gösterildi.")

            st.success("Tur-3 görselleştirme ve analiz tamamlandı.")
else:
    secure_delete(["tur3_api"])
