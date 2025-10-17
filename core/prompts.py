
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
    return f"""
    You are an actuarial data QA consultant. Given the dataset summary (from an Excel produced in Turn-1)
    and the initial EDA, propose an OUTLIER analysis plan specifically for cumulative claims triangles.
    Cover:
    - pointwise outliers on incremental amounts (IQR/Tukey, z-score, robust MAD),
    - outliers on age-to-age factors (IQR and robust methods),
    - EVT/POT with Hill estimator for heavy tails (outline steps, threshold selection, diagnostics),
    - time-dependence checks (AY/devQ structure),
    - practical thresholds and step-by-step workflow.
    Output JSON with keys: methods[], thresholds[], workflow[], notes.
    EXCEL_SUMMARY_JSON: {json.dumps(excel_summary, ensure_ascii=False)}
    EDA_JSON: {json.dumps(eda_result, ensure_ascii=False)}
    """

def prompt_tur3(df_norm, tur1_out, tur2_out) -> str:
    sample = df_norm.head(50).to_dict(orient="records")
    return f"""
    You are an actuarial analyst. From the suggested methods decide ONE applicable analysis and
    produce a short plan (<=120 words) for visuals and interpretation. Prefer an analysis that can
    be computed locally (e.g., IQR on age-to-age or incremental). Return JSON:
    {{
      "chosen_method": "<name>",
      "reason": "<short>",
      "visuals": ["<chart suggestion>", "..."],
      "interpretation_focus": ["<bullets>"]
    }}
    CONTEXT_TUR1={json.dumps(tur1_out, ensure_ascii=False)}
    CONTEXT_TUR2={json.dumps(tur2_out, ensure_ascii=False)}
    SAMPLE_ROWS={json.dumps(sample, ensure_ascii=False)}
    """
