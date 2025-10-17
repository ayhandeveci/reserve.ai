
# reserveai — Kasko Hasar (Cumulative) Üç-Turlu Analiz

**Akış**
1. **Tur-1 (EDA):** CSV veya örnek veri yükle → temel EDA + data quality notları (JSON).
2. **Tur-2 (Öneriler):** Orijinal normalize veri + Tur-1 çıktısı → LLM tabanlı öneriler (JSON).
3. **Tur-3 (Görselleştirme):** Tur-1&2 çıktıları + veri → grafikler (LLM viz-spec varsa uyum sağlar).

**Güvenlik**
- Her section kendi API anahtarını alır ve **section toggle kapanınca hafızadan silinir**.
- Uygulama LLM olmadan da çalışır; internet yoksa demo iskeleti üretir.

**Çalıştırma**
```bash
pip install -r requirements.txt
streamlit run app.py
```

**Örnek veri**
- `assets/kasko_cumulative_claims_sample.csv`


## Update
- Tur-1: Excel raporu (çoklu sayfa + bar chart) ve indirme butonu eklendi.
- Tur-2: Tur-1 Excel tekrar içeri alınabiliyor; LLM promptu outlier metodolojileri (IQR, z-score, MAD, EVT/Hill) için güncellendi.
- Tur-3: IQR ile age-to-age outlier uygulaması ve görselleştirmesi eklendi.
