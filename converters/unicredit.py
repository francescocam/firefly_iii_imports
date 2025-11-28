#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, List
import re


def _parse_decimal_it(value: str) -> Decimal:
    """
    Parse Italian-formatted decimal string to Decimal.

    Handles Italian number formatting where comma is the decimal separator
    and period is the thousands separator.

    Args:
        value: String representation of a decimal number in Italian format.

    Returns:
        Decimal representation of the input value. Returns Decimal("0") for
        empty strings, None values, or invalid inputs.

    Examples:
        >>> _parse_decimal_it("-33,67")
        Decimal('-33.67')
        >>> _parse_decimal_it("1.234,56")
        Decimal('1234.56')
        >>> _parse_decimal_it("")
        Decimal('0')
        >>> _parse_decimal_it(None)
        Decimal('0')
    """
    if value is None:
        return Decimal("0")
    s = str(value).strip()
    if not s:
        return Decimal("0")
    # Remove thousands separator and replace decimal comma
    s = s.replace(".", "").replace(",", ".")
    try:
        return Decimal(s)
    except InvalidOperation:
        # Fallback: try to remove any stray spaces or non-digits
        filtered = "".join(ch for ch in s if ch in "-+.0123456789")
        return Decimal(filtered or "0")


def _determine_opposing_name(description: str) -> str:
    """
    Determine the opposing account name based on transaction description.

    Args:
        description: Transaction description from Unicredit CSV.

    Returns:
        Opposing account name based on description patterns.
    """
    desc = description.strip()

    if "COMPETENZE (INTERESSI/ONERI)" in desc:
        return "spese conto unicredit"
    elif "RICARICA CONTO" in desc:
        return "spese conto unicredit"
    elif "GENIUS SUPER GENIUS 2.0: COSTO FISSO" in desc:
        return "spese conto unicredit"
    elif "BONIFICO" in desc and "CAMISA FRANCESCO" in desc:
        return "fineco"
    elif "FINANZIAMENTO 000/4500287/000" in desc:
        return "mutuo ristrutturazione"
    elif "FINANZIAM. NUMERO: 0000000014308394" in desc:
        return "chirografario ristrutturazione"
    else:
        return "to be inputed"


def convert_unicredit_csv_to_firefly(
    input_csv: Path | str,
    output_csv: Path | str,
    config: dict,
) -> int:
    """
    Convert Unicredit CSV to Firefly III import format.

    Processes Unicredit CSV files with Italian decimal formatting and
    determines opposing account names based on transaction descriptions.

    Args:
        input_csv: Path to the input Unicredit CSV file.
        output_csv: Path where the output Firefly III CSV will be written.
        config: Configuration dictionary containing Unicredit-specific settings.

    Returns:
        Number of rows processed.

    Raises:
        ValueError: If required Unicredit configuration keys are missing or invalid.

    Example:
        >>> config = {
        ...     "unicredit": {
        ...         "account_name": "unicredit",
        ...         "output_columns": ["date_transaction", "amount", "description", "opposing-name", "account-name"]
        ...     }
        ... }
        >>> processed = convert_unicredit_csv_to_firefly("input.csv", "output.csv", config)
        >>> print(f"Processed {processed} transactions")
    """
    try:
        unicredit_config = config["unicredit"]
    except KeyError as exc:
        raise ValueError("Missing 'unicredit' section in configuration.") from exc

    required_keys = ["account_name", "output_columns"]
    missing_keys = [key for key in required_keys if key not in unicredit_config]
    if missing_keys:
        raise ValueError(
            "Missing required Unicredit configuration keys: " + ", ".join(missing_keys)
        )

    output_columns = unicredit_config["output_columns"]
    if not isinstance(output_columns, list) or not output_columns:
        raise ValueError("'unicredit.output_columns' must be a non-empty list.")

    input_csv = Path(input_csv)
    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    # Read CSV with semicolon delimiter (Italian format)
    with input_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=';')
        rows: List[Dict[str, str]] = list(reader)

    out_rows: List[Dict[str, str]] = []

    for row in rows:
        # Extract required fields
        data_valuta = (row.get("Data valuta") or "").strip()
        descrizione = re.sub(r'\s+', ' ', (row.get("Descrizione") or "")).strip()
        importo_eur = (row.get("Importo (EUR)") or "").strip()

        # Skip header or empty rows
        if not data_valuta or not descrizione or not importo_eur:
            continue

        # Parse amount using Italian decimal format
        amount_val = _parse_decimal_it(importo_eur)

        # Determine opposing name based on description
        opposing_name = _determine_opposing_name(descrizione)

        # Create output row in Firefly III format
        out_rows.append(
            {
                "account-name": unicredit_config["account_name"],
                "date_transaction": data_valuta,
                "amount": format(amount_val, "f"),
                "description": descrizione,
                "opposing-name": opposing_name,
            }
        )

    # Write output
    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=output_columns)
        writer.writeheader()
        writer.writerows(out_rows)

    return len(out_rows)
