from __future__ import annotations

import csv
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from pathlib import Path
from typing import Dict, List


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


def convert_paypal_csv_to_firefly(
    input_csv: Path | str,
    output_csv: Path | str,
    config: dict,
) -> List[Dict[str, str]]:
    """
    Convert PayPal CSV to Firefly III import format.

    Processes PayPal CSV files with paired or unpaired transaction rows.
    Handles currency conversion transactions.

    Args:
        input_csv: Path to the input PayPal CSV file.
        output_csv: Path where the output Firefly III CSV will be written.
        config: Configuration dictionary containing PayPal-specific settings.

    Returns:
        Empty list (no orphan rows are identified).

    Raises:
        ValueError: If required PayPal configuration keys are missing or invalid.

    Example:
        >>> config = {
        ...     "paypal": {
        ...         "source_account": "PayPal",
        ...         "output_columns": ["date", "description", "amount", "source_account", "destination_account"],
        ...         "positive_is_withdrawal": True
        ...     }
        ... }
        >>> convert_paypal_csv_to_firefly("input.csv", "output.csv", config)
    """
    try:
        paypal_config = config["paypal"]
    except KeyError as exc:
        raise ValueError("Missing 'paypal' section in configuration.") from exc

    required_keys = [
        "source_account",
        "output_columns",
    ]
    missing_keys = [key for key in required_keys if key not in paypal_config]
    if missing_keys:
        raise ValueError(
            "Missing required PayPal configuration keys: " + ", ".join(missing_keys)
        )

    output_columns = paypal_config["output_columns"]
    if not isinstance(output_columns, list) or not output_columns:
        raise ValueError("'paypal.output_columns' must be a non-empty list.")

    positive_is_withdrawal = paypal_config.get("positive_is_withdrawal", True)
    if not isinstance(positive_is_withdrawal, bool):
        raise ValueError("'paypal.positive_is_withdrawal' must be a boolean if provided.")

    input_csv = Path(input_csv)
    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    # Read all rows preserving order; handle UTF-8 with BOM
    with input_csv.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows: List[Dict[str, str]] = list(reader)

    out_rows: List[Dict[str, str]] = []

    i = 0
    n = len(rows)
    while i < n:
        row = rows[i]
        name = (row.get("Nome") or "").strip()

        # Skip rows that are not transaction headers (empty "Nome" field)
        if not name:
            i += 1
            continue

        # Check if there's a following accounting row (no "Nome")
        if i + 1 < n and not (rows[i + 1].get("Nome") or "").strip():
            # Paired: use the next row for transaction data
            row_data = rows[i + 1]
            i += 2
            # For paired rows, negate the amount for Firefly III format
            negate = True
        else:
            # Unpaired: use the current row for transaction data
            row_data = row
            i += 1
            # For unpaired rows, negate the amount as per user request
            negate = True

        # Extract transaction details from row_data
        date_str = (row_data.get("Data") or "").strip()
        amount_raw = (row_data.get("Importo") or "").strip()
        amount_val = _parse_decimal_it(amount_raw)

        # Apply negation if required
        if negate:
            amount_out = (-amount_val).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        else:
            amount_out = amount_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)

        # Create output row in Firefly III format
        out_rows.append(
            {
                "date_transaction": date_str,
                "description": name,
                "amount": format(amount_out, "f"),
                "account-name": paypal_config["source_account"],
                "opposing-name": name,
            }
        )

        # Handle currency conversion transactions which may have additional rows
        # Skip conversion lines that have empty "Nome" and "Tipo" starting with "Conversione di valuta generica"
        while i < n and not (rows[i].get("Nome") or "").strip():
            tipo = (rows[i].get("Tipo") or "").strip()
            if tipo.startswith("Conversione di valuta generica"):
                i += 1
                continue
            # Not a conversion line; leave for the next iteration
            break

    # Write output
    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=output_columns)
        writer.writeheader()
        writer.writerows(out_rows)

    return []
