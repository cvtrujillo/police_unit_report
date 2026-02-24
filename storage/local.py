import pandas as pd
from pathlib import Path


def save_excel(plp_df: pd.DataFrame, pdp_df: pd.DataFrame, run_ts: str) -> str:
    path = f"inventory_{run_ts}.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        plp_df.to_excel(writer, sheet_name="PLP_Resumen", index=False)
        if not pdp_df.empty:
            pdp_df.to_excel(writer, sheet_name="PDP_Criticos", index=False)
    return path
