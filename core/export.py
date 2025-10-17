
import pandas as pd
import numpy as np
from io import BytesIO

def build_tur1_summary(df: pd.DataFrame) -> dict:
    info = {}
    info["shape"] = {"rows": int(df.shape[0]), "cols": int(df.shape[1])}
    dtypes = df.dtypes.astype(str).to_dict()
    nulls = df.isna().sum().to_dict()
    uniques = {c: int(df[c].nunique(dropna=True)) for c in df.columns}
    # numeric columns
    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    sums = {c: float(pd.to_numeric(df[c], errors="coerce").sum()) for c in num_cols}
    # segment candidates = low-cardinality columns (<=12 unique) or categorical-like
    seg_candidates = []
    for c in df.columns:
        try:
            u = uniques[c]
            if u>1 and u<=12:
                seg_candidates.append({"column": c, "unique": int(u)})
        except Exception:
            pass
    # age-to-age on incurred
    ata = {}
    try:
        piv = df.pivot_table(index="accident_year", columns="development_quarter", values="incurred_cum", aggfunc="last")
        piv = piv.sort_index()
        for j in range(1, piv.shape[1]):
            num = piv.get(j+1, pd.Series()).sum(skipna=True)
            den = piv.get(j, pd.Series()).sum(skipna=True)
            if den and den != 0:
                ata[f"{j}->{j+1}"] = float(num/den)
    except Exception:
        ata = {}
    return {
        "shape": info["shape"],
        "dtypes": dtypes,
        "null_counts": {k:int(v) for k,v in nulls.items()},
        "unique_counts": uniques,
        "numeric_sums": sums,
        "segment_candidates": seg_candidates,
        "age_to_age_incurred": ata
    }

def export_tur1_excel(df: pd.DataFrame, summary: dict) -> BytesIO:
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="xlsxwriter") as xw:
        # Sheets
        pd.DataFrame([summary["shape"]]).to_excel(xw, sheet_name="Summary", index=False)
        meta = pd.DataFrame({
            "column": list(summary["dtypes"].keys()),
            "dtype": list(summary["dtypes"].values()),
            "nulls": [summary["null_counts"].get(c,0) for c in summary["dtypes"].keys()],
            "unique": [summary["unique_counts"].get(c,0) for c in summary["dtypes"].keys()],
        })
        meta.to_excel(xw, sheet_name="Columns", index=False)
        pd.DataFrame(list(summary["numeric_sums"].items()), columns=["column","sum"]).to_excel(xw, sheet_name="NumericSums", index=False)
        pd.DataFrame(summary["segment_candidates"]).to_excel(xw, sheet_name="Segments", index=False)
        if summary.get("age_to_age_incurred"):
            pd.DataFrame(list(summary["age_to_age_incurred"].items()), columns=["age_to_age","factor"]).to_excel(xw, sheet_name="AgeToAge", index=False)

        # Add a couple of charts using xlsxwriter
        wb  = xw.book
        # Chart 1: Numeric sums bar (top 10)
        try:
            ns = pd.DataFrame(list(summary["numeric_sums"].items()), columns=["column","sum"]).sort_values("sum", ascending=False).head(10)
            ns_sheet = wb.add_worksheet("ChartData")
            for r,(cname,s) in enumerate(ns.values.tolist(), start=1):
                ns_sheet.write(r,0,cname); ns_sheet.write(r,1,float(s))
            chart = wb.add_chart({"type":"column"})
            chart.add_series({
                "name": "Numeric sums (top10)",
                "categories": ["ChartData", 1, 0, len(ns), 0],
                "values": ["ChartData", 1, 1, len(ns), 1]
            })
            chart.set_title({"name":"Numeric column sums (top 10)"})
            wb.get_worksheet_by_name("Summary").insert_chart(5, 0, chart)
        except Exception:
            pass
    bio.seek(0)
    return bio
