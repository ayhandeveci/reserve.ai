
import pandas as pd
import streamlit as st

def load_input_data(file_or_path):
    if file_or_path is None:
        return None
    if isinstance(file_or_path, str):
        return pd.read_csv(file_or_path)
    return pd.read_csv(file_or_path)

def normalize_triangle_like(df: pd.DataFrame):
    notes = []
    # Column normalization / renaming tolerant read
    rename_map = {
        "accident_year":"accident_year",
        "development_quarter":"development_quarter",
        "incurred_cum":"incurred_cum",
        "paid_cum":"paid_cum",
        "reported_claims_cum":"reported_claims_cum",
        "ultimate_incurred":"ultimate_incurred",
        "exposure_policies":"exposure_policies",
        "ultimate_claims":"ultimate_claims",
        "line_of_business":"line_of_business",
        "valuation_quarter":"valuation_quarter",
    }
    missing = [c for c in ["accident_year","development_quarter","incurred_cum","paid_cum"] if c not in df.columns]
    if missing:
        notes.append(f"Beklenen kolonlar eksik: {missing}")
    # type handling
    for col in ["accident_year","development_quarter","ultimate_claims","reported_claims_cum","exposure_policies"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
    for col in ["incurred_cum","paid_cum","ultimate_incurred"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.sort_values(["accident_year","development_quarter"], na_position="last").reset_index(drop=True)
    return df, notes
