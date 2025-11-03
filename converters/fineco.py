#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from pathlib import Path

import numpy as np
import pandas as pd


def _validate_fineco_config(config: dict) -> dict:
    try:
        fineco_config = config["fineco"]
    except KeyError as exc:
        raise ValueError("Missing 'fineco' section in configuration.") from exc

    required_keys = [
        "default_account",
        "header_row",
        "required_columns",
        "currency_code",
        "card_a",
        "card_b",
    ]
    missing = [key for key in required_keys if key not in fineco_config]
    if missing:
        raise ValueError(
            "Missing required Fineco configuration keys: " + ", ".join(missing)
        )

    required_columns = fineco_config["required_columns"]
    if not isinstance(required_columns, (list, tuple)) or not required_columns:
        raise ValueError("'fineco.required_columns' must be a non-empty list.")

    return fineco_config


def prepare_fineco_csv(input_path: Path, output_path: Path, config: dict) -> int:
    """
    Convert Fineco Excel file to Firefly III CSV format.

    Args:
        input_path: Path to input Excel file
        output_path: Path to output CSV file
        config: Configuration dictionary with Fineco settings

    Returns:
        Number of rows dropped because of missing date or amount values.
    """
    fineco_config = _validate_fineco_config(config)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelFile(input_path, engine="openpyxl") as xls:
        sheet_name = xls.sheet_names[0]
        try:
            head = xls.parse(sheet_name, nrows=1)
            if not head.empty:
                default_account = str(head.iloc[0, 0]).strip()
            else:
                default_account = fineco_config["default_account"]
        except Exception:
            default_account = fineco_config["default_account"]

        df = xls.parse(sheet_name, header=fineco_config["header_row"])

    required = fineco_config["required_columns"]
    if not set(required).issubset(df.columns):
        missing_columns = [c for c in required if c not in df.columns]
        raise ValueError(f"Colonne richieste mancanti: {missing_columns}")

    entrate = pd.to_numeric(df.get("Entrate"), errors="coerce")
    uscite = pd.to_numeric(df.get("Uscite"), errors="coerce")
    amt = entrate.fillna(0) - uscite.fillna(0)

    date = pd.to_datetime(df["Data_Valuta"], errors="coerce").dt.date
    descr_base = df["Descrizione"].fillna(df["Descrizione_Completa"]).fillna("Transazione")
    descr_full = df["Descrizione_Completa"].fillna(df["Descrizione"]).fillna("Transazione")

    dstr = df["Descrizione"].astype(str).str.strip()
    mask_a = dstr == fineco_config["card_a"]
    mask_b = dstr == fineco_config["card_b"]

    row_account = np.where(
        mask_a,
        fineco_config["card_a"],
        np.where(mask_b, fineco_config["card_b"], default_account),
    )
    description = np.where(mask_a | mask_b, descr_full, descr_base)
    payee = descr_full

    output_data = {
        "date": date,
        "description": description,
        "amount": amt.abs().round(2),
        "currency_code": fineco_config["currency_code"],
        "type": np.where(amt < 0, "withdrawal", "deposit"),
        "source_name": np.where(amt < 0, row_account, payee),
        "destination_name": np.where(amt < 0, payee, row_account),
        "category": pd.NA,
        "notes": df["Descrizione_Completa"],
        "tags": pd.NA,
        "external_id": pd.NA,
    }

    out = pd.DataFrame(output_data)
    before_drop = len(out)
    out = out.dropna(subset=["date", "amount"])
    dropped = before_drop - len(out)

    out.to_csv(output_path, index=False, encoding="utf-8")

    return dropped


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

    dropped_rows = prepare_fineco_csv(Path(args.input), Path(args.output), config)
    if dropped_rows:
        print(
            f"Skipped {dropped_rows} transaction(s) lacking date or amount information.",
            flush=True,
        )
