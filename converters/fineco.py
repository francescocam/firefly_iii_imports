#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from pathlib import Path
import pandas as pd
import numpy as np


def prepare_fineco_csv(input_path: Path, output_path: Path, config: dict) -> None:
    """
    Convert Fineco Excel file to Firefly III CSV format.

    Args:
        input_path: Path to input Excel file
        output_path: Path to output CSV file
        config: Configuration dictionary with Fineco settings
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fineco_config = config["fineco"]

    xls = pd.ExcelFile(input_path)
    try:
        head = xls.parse(xls.sheet_names[0], nrows=1)
        default_account = str(head.iloc[0, 0]).strip() if not head.empty else fineco_config["default_account"]
    except Exception:
        default_account = fineco_config["default_account"]

    df = pd.read_excel(input_path, header=fineco_config["header_row"])

    required = fineco_config["required_columns"]
    if not set(required).issubset(df.columns):
        missing = [c for c in required if c not in df.columns]
        raise ValueError(f"Colonne richieste mancanti: {missing}")

    entrate = pd.to_numeric(df.get("Entrate"), errors="coerce")
    uscite = pd.to_numeric(df.get("Uscite"), errors="coerce")
    amt = entrate.fillna(0) - uscite.fillna(0)

    date = pd.to_datetime(df["Data_Valuta"], errors="coerce").dt.date
    descr_base = df["Descrizione"].fillna(df["Descrizione_Completa"]).fillna("Transazione")
    descr_full = df["Descrizione_Completa"].fillna(df["Descrizione"]).fillna("Transazione")

    dstr = df["Descrizione"].astype(str).str.strip()
    mask_a = dstr == fineco_config["card_a"]
    mask_b = dstr == fineco_config["card_b"]

    row_account = np.where(mask_a, fineco_config["card_a"], np.where(mask_b, fineco_config["card_b"], default_account))
    description = np.where(mask_a | mask_b, descr_full, descr_base)
    payee = descr_full

    out = pd.DataFrame()
    out["date"] = date
    out["description"] = description
    out["amount"] = amt.abs().round(2)
    out["currency_code"] = fineco_config["currency_code"]
    out["type"] = np.where(amt < 0, "withdrawal", "deposit")
    out["source_name"] = np.where(amt < 0, row_account, payee)
    out["destination_name"] = np.where(amt < 0, payee, row_account)
    out["category"] = pd.NA
    out["notes"] = df["Descrizione_Completa"]
    out["tags"] = pd.NA
    out["external_id"] = pd.NA

    out = out.dropna(subset=["date", "amount"])
    out.to_csv(output_path, index=False, encoding="utf-8")


if __name__ == "__main__":
    # For backward compatibility when run directly
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Percorso file Excel in input")
    ap.add_argument("--output", required=True, help="Percorso CSV in output")
    ap.add_argument("--config", default="config/config.json", help="Percorso file configurazione JSON")
    args = ap.parse_args()

    with open(args.config, 'r', encoding='utf-8') as f:
        config = json.load(f)

    prepare_fineco_csv(Path(args.input), Path(args.output), config)