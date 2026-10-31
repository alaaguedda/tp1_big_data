"""Task 1 + Task 2: profile the sample, then clean and transform it.

Input : data/HIGGS_sample_1pct.csv  (needs columns lepton_pT and m_bb)
Output: output/higgs_clean.csv      (import this file in Power BI)
        output/profile.txt          (rows, types, missing, duplicates: for the report)
"""
import os
import numpy as np
import pandas as pd

INPUT_FILE = os.environ.get("INPUT_FILE", "data/HIGGS_sample_1pct.csv")
CLEAN_FILE = "output/higgs_clean.csv"
PROFILE_FILE = "output/profile.txt"
PT_THRESHOLD = float(os.environ.get("PT_THRESHOLD", "1.0"))
BIN_SIZE = float(os.environ.get("BIN_SIZE", "0.25"))
CLIP_AT = 4.0

df = pd.read_csv(INPUT_FILE)
for col in ("lepton_pT", "m_bb"):
    if col not in df.columns:
        raise SystemExit(f"Column '{col}' not found. Columns are: {list(df.columns)[:10]}...")

lines = []
lines.append("TASK 1: PROFILE OF THE IMPORTED DATA")
lines.append(f"File: {INPUT_FILE}")
lines.append(f"Rows: {len(df):,} | Columns: {df.shape[1]}")
lines.append("")
lines.append("Column / type / missing values")
for c in df.columns:
    lines.append(f"  {c:28s} {str(df[c].dtype):10s} missing={int(df[c].isna().sum())}")
dups = int(df.duplicated().sum())
lines.append("")
lines.append(f"Duplicated rows: {dups:,}")

# ---- Task 2: clean and transform
rows_before = len(df)
df = df.drop_duplicates()
after_dups = len(df)
df = df.dropna(subset=["lepton_pT", "m_bb"])
after_na = len(df)

df["pT_level"] = np.where(df["lepton_pT"] < PT_THRESHOLD, "Low", "High")
df["pT_bin"] = (np.floor(df["lepton_pT"].clip(upper=CLIP_AT) / BIN_SIZE) * BIN_SIZE).round(2)
df["m_bb_bin"] = (np.floor(df["m_bb"].clip(upper=CLIP_AT) / BIN_SIZE) * BIN_SIZE).round(2)
if "label" in df.columns:
    df["event_type"] = np.where(df["label"] == 1, "Signal", "Background")

lines.append("")
lines.append("TASK 2: CLEANING")
lines.append(f"Rows before: {rows_before:,}")
lines.append(f"After removing duplicates: {after_dups:,} (removed {rows_before - after_dups:,})")
lines.append(f"After removing missing lepton_pT / m_bb: {after_na:,} (removed {after_dups - after_na:,})")
lines.append(f"New columns: pT_level (Low if lepton_pT < {PT_THRESHOLD}), pT_bin, m_bb_bin"
             + (", event_type" if "event_type" in df.columns else ""))

os.makedirs("output", exist_ok=True)
df.to_csv(CLEAN_FILE, index=False)
with open(PROFILE_FILE, "w") as f:
    f.write("\n".join(lines) + "\n")
print("\n".join(lines))
print(f"\nSaved {CLEAN_FILE} and {PROFILE_FILE}")
