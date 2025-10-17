import json

def prompt_tur1(eda_result: dict) -> str:
    return f"""
    You are an actuarial assistant focusing on Auto Hull (Kasko) cumulative claims.
    Summarize this EDA in <=150 words. Emphasize: shape, numeric totals, low-cardinality
    segments, monotonicity, and material age-to-age signals.
    EDA_JSON:
    {json.dumps(eda_result, ensure_ascii=False)}
    """

def prompt_tur2_from_excel(excel_summary: dict, eda_result: dict) -> str:
    # Açık ve seçilebilir bir öneri istiyoruz: top_recommendation zorunlu
    return f"""
    You are an actuarial data QA consultant. Given the Turn-1 dataset summary (from Excel) and EDA,
    propose an OUTLIER analysis plan for cumulative claims triangles.

    Cover methods (with when to use and parameter hints):
      - IQR/Tukey (on incremental losses and on age-to-age factors),
      - z-score / robust MAD,
      - EVT (POT) with Hill estimator (outline thresholding and diagnostics).

    Return STRICT JSON with keys:
    {{
      "top_recommendation": {{
        "method": "<short name>",
        "why": "<1-2 sentences>",
        "when_to_use": "<conditions>",
        "parameters": [{{"name":"param","hint":"how to choose"}}, ...]
      }},
      "alternatives": [{{"method":"...", "why":"..."}}, ...],
      "workflow": ["step 1", "step 2", "..."],
      "notes": "<free text>"
    }}

    EXCEL_SUMMARY_JSON: {json.dumps(excel_summary, ensure_ascii=False)}
    EDA_JSON: {json.dumps(eda_result, ensure_ascii=False)}
    """

def prompt_tur3(df_norm, tur1_out, tur2_out) -> str:
    # Tur-3: anlatımı zenginleştirmek için kısa plan istiyoruz
    sample = df_norm.head(40).to_dict(orient="records")
    return f"""
    You are an actuarial analyst. Using the Turn-2 recommendation, choose ONE method (prefer the 'top_recommendation')
    and produce a concise narrative (<=120 words) including:
    - chosen_method,
    - reason,
    - what the charts show,
    - how to interpret flags and next actions.

    Return JSON:
    {{
      "chosen_method": "<name>",
      "reason": "<short>",
      "narrative": "<<=120 words>"
    }}

    TUR1={json.dumps(tur1_out, ensure_ascii=False)}
    TUR2={json.dumps(tur2_out, ensure_ascii=False)}
    SAMPLE_ROWS={json.dumps(sample, ensure_ascii=False)}
    """
