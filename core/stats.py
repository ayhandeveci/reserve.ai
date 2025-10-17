
import pandas as pd
import numpy as np
from .export import build_tur1_summary

def run_basic_eda(df: pd.DataFrame) -> dict:
    # keep previous checks + enhanced summary
    out = build_tur1_summary(df)
    # add monotonic flags explicitly
    checks = {}
    for col in ["incurred_cum","paid_cum","reported_claims_cum"]:
        if col in df.columns:
            bad = []
            for ay, g in df.groupby("accident_year", dropna=True):
                vals = g[col].fillna(0).values
                if np.any(np.diff(vals) < 0):
                    bad.append(int(ay))
            checks[col+"_nondecreasing"] = {"ok": len(bad)==0, "violations_by_AY": bad}
    out["monotonicity"] = checks
    # dev coverage by AY
    if "development_quarter" in df.columns:
        coverage = df.groupby("accident_year")["development_quarter"].max().to_dict()
        out["dev_quarter_max_by_AY"] = {int(k): int(v) for k,v in coverage.items()}
    return out
