#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from pathlib import Path

import numpy as np
import pandas as pd


def _validate_fineco_config(config: dict) -> dict:
    """
    Validate and extract Fineco configuration from the main config dictionary.

    Args:
        config: Main configuration dictionary containing 'fineco' section.

    Returns:
        Validated Fineco configuration dictionary.

    Raises:
        ValueError: If 'fineco' section is missing or required keys are absent/invalid.
    """
    try:
        fineco_config = config["fineco"]
    except KeyError as exc:
        raise ValueError("Missing 'fineco' section in configuration.") from exc

    required_keys = [
        "fineco_account",
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

    This function reads a Fineco Excel file, processes the transaction data,
    and outputs a CSV file compatible with Firefly III import format.

    Args:
        input_path: Path to the input Excel file (.xlsx format)
        output_path: Path where the output CSV file will be written
        config: Configuration dictionary containing Fineco-specific settings

    Returns:
        Number of rows dropped due to missing date or amount values.

    Raises:
        ValueError: If required configuration keys are missing or invalid,
                   or if required columns are not present in the Excel file.

    Example:
        >>> from pathlib import Path
        >>> config = {
        ...     "fineco": {
        ...         "fineco_account": "Fineco Account",
        ...         "header_row": 0,
        ...         "required_columns": ["Data_Valuta", "Descrizione", "Entrate", "Uscite"],
        ...         "currency_code": "EUR",
        ...         "card_a": {"number": "<card number as it appears in the transactions>", "source_account_name": "fineco carta prepagata"},
        ...         "card_b": {"number": "5127 **** **** 2119", "source_account_name": "fineco carta credito"}
        ...     }
        ... }
        >>> dropped = prepare_fineco_csv(Path("input.xlsx"), Path("output.csv"), config)
        >>> print(f"Conversion complete, {dropped} rows dropped")
    """
    fineco_config = _validate_fineco_config(config)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelFile(input_path, engine="openpyxl") as xls:
        sheet_name = xls.sheet_names[0]
        try:
            fineco_account = fineco_config["fineco_account"]
        except Exception:
            fineco_account = fineco_config["fineco_account"]

        df = xls.parse(sheet_name, header=fineco_config["header_row"])

    # Validate that all required columns are present in the DataFrame
    required = fineco_config["required_columns"]
    if not set(required).issubset(df.columns):
        missing_columns = [c for c in required if c not in df.columns]
        raise ValueError(f"Colonne richieste mancanti: {missing_columns}")

    # Calculate transaction amounts: positive for deposits (entrate), negative for withdrawals (uscite)
    entrate = pd.to_numeric(df["Entrate"], errors="coerce")
    uscite = pd.to_numeric(df["Uscite"], errors="coerce")
    amt = entrate.fillna(0) + uscite.fillna(0)

    # Extract and process date information
    date = pd.to_datetime(df["Data_Valuta"], errors="coerce").dt.date

    # Handle description fields with fallbacks
    descr_base = df["Descrizione"].fillna(df["Descrizione_Completa"]).fillna("Transazione")
    descr_full = df["Descrizione_Completa"].fillna(df["Descrizione"]).fillna("Transazione")

    # Identify card-specific transactions
    dstr = df["Descrizione"].astype(str).str.strip()
    mask_a = dstr.str.contains(fineco_config["card_a"]["number"])
    mask_b = dstr.str.contains(fineco_config["card_b"]["number"])

    # Determine account names based on card type
    source_account_name = np.where(
        mask_a,
        fineco_config["card_a"]["source_account_name"],
        np.where(mask_b, fineco_config["card_b"]["source_account_name"], fineco_account),
    )
    # Always use full description
    description = descr_full
    destination_account_name = descr_full

    output_data = {
        "date": date,
        "description": description,
        "amount": amt.abs().round(2),
        "currency_code": fineco_config["currency_code"],
        "type": np.where(amt < 0, "withdrawal", "deposit"),
        "source_name": source_account_name,
        "destination_name": destination_account_name,
        "category": pd.NA,
        "notes": df["Descrizione"],
        "tags": pd.NA,
        "external_id": pd.NA,
    }

    out = pd.DataFrame(output_data)
    before_drop = len(out)
    out = out.dropna(subset=["date", "amount"])
    dropped = before_drop - len(out)

    out.to_csv(output_path, index=False, encoding="utf-8")

    return dropped


