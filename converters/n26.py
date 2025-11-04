#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
from pathlib import Path


def _validate_n26_config(config: dict) -> dict:
    """
    Validate and extract N26 configuration from the main config dictionary.

    Args:
        config: Main configuration dictionary containing 'n26' section.

    Returns:
        Validated N26 configuration dictionary.

    Raises:
        ValueError: If 'n26' section is missing or required keys are absent/invalid.
    """
    try:
        n26_config = config["n26"]
    except KeyError as exc:
        raise ValueError("Missing 'n26' section in configuration.") from exc

    required_keys = ["account_name"]
    missing = [key for key in required_keys if key not in n26_config]
    if missing:
        raise ValueError(
            "Missing required N26 configuration keys: " + ", ".join(missing)
        )

    return n26_config


def convert_n26_csv_to_firefly(input_path: Path, output_path: Path, config: dict) -> int:
    """
    Convert N26 CSV file to Firefly III CSV format.

    This function reads an N26 CSV file, processes the transaction data,
    and outputs a CSV file compatible with Firefly III import format.

    Args:
        input_path: Path to the input N26 CSV file
        output_path: Path where the output CSV file will be written
        config: Configuration dictionary containing N26-specific settings

    Returns:
        Number of rows dropped due to missing date or amount values.

    Raises:
        ValueError: If required configuration keys are missing or invalid,
                   or if required columns are not present in the CSV file.

    Example:
        >>> from pathlib import Path
        >>> config = {
        ...     "n26": {
        ...         "account_name": "N26"
        ...     }
        ... }
        >>> dropped = convert_n26_csv_to_firefly(Path("n26.csv"), Path("output.csv"), config)
        >>> print(f"Conversion complete, {dropped} rows dropped")
    """
    n26_config = _validate_n26_config(config)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Read CSV file
    df = pd.read_csv(input_path)

    # Validate required columns
    required_columns = ["Value Date", "Partner Name", "Partner Iban", "Payment Reference", "Amount (EUR)"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Required columns missing from N26 CSV: {missing_columns}")

    # Extract and process data
    date_transaction = pd.to_datetime(df["Value Date"], errors="coerce").dt.date

    # Handle opposing-name: Partner Name if not empty, otherwise Payment Reference
    partner_name = df["Partner Name"].fillna("")
    payment_ref = df["Payment Reference"].fillna("")
    opposing_name = partner_name.where(partner_name != "", payment_ref)

    # Amount processing - keep as is (negative for withdrawals, positive for deposits)
    amount = pd.to_numeric(df["Amount (EUR)"], errors="coerce")

    # Description: Combine Partner Iban and Payment Reference
    partner_iban = df["Partner Iban"].fillna("")
    description = partner_iban + " " + payment_ref
    description = description.str.strip()

    # Determine transaction type based on amount sign
    # In Firefly III: withdrawal = money leaving account, deposit = money entering account
    # N26: negative amounts = withdrawals (money leaving), positive = deposits (money entering)
    transaction_type = pd.Series("withdrawal", index=df.index)
    transaction_type[amount > 0] = "deposit"

    # Create output DataFrame in Firefly III format
    output_data = {
        "date_transaction": date_transaction,
        "opposing-name": opposing_name,
        "amount": amount.abs().round(2),  # Use absolute value for amount field
        "description": description,
        "account-name": n26_config["account_name"],
        # Additional Firefly III fields (can be empty)
        "notes": pd.NA,
        "currency_code": "EUR",
        "type": transaction_type,
        "category": pd.NA,
        "tags": pd.NA,
        "external_id": pd.NA,
    }

    out = pd.DataFrame(output_data)

    # Drop rows with missing date or amount
    before_drop = len(out)
    out = out.dropna(subset=["date_transaction", "amount"])
    dropped = before_drop - len(out)

    # Write to CSV
    out.to_csv(output_path, index=False, encoding="utf-8")

    return dropped