from __future__ import annotations

import csv
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, List


def _parse_decimal_it(value: str) -> Decimal:
    """Parse Italian-formatted decimal string to Decimal.

    Examples:
    - "-33,67" -> Decimal("-33.67")
    - "1.234,56" -> Decimal("1234.56")
    - "" or None -> Decimal("0")
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
) -> None:
    """
    Convert PayPal CSV to Firefly III import format.

    Args:
        input_csv: Path to input PayPal CSV file
        output_csv: Path to output CSV file for Firefly III import
        config: Configuration dictionary with PayPal settings
    """
    paypal_config = config["paypal"]
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

        # If this row is not a transaction head, advance
        if not name:
            i += 1
            continue

        # Expect the immediate next row to be the paired accounting line
        if i + 1 >= n:
            break
        row2 = rows[i + 1]

        # Extract fields from the second row as per spec
        date_str = (row2.get("Data") or "").strip()
        currency = (row2.get("Valuta") or "").strip()
        amount_raw = (row2.get("Importo") or "").strip()
        amount_val = _parse_decimal_it(amount_raw)

        # Business rule from user: positive amount -> withdrawal, else deposit
        tx_type = "withdrawal" if amount_val > 0 else "deposit"

        out_rows.append(
            {
                "date": date_str,
                "description": name,
                "amount": str(-amount_val),
                "currency_code": currency,
                "type": tx_type,
                "source_account": paypal_config["source_account"],
                "destination_account": name,
            }
        )

        # Skip the paired row
        i += 2

        # For 4-row transactions (currency conversion), skip the following
        # conversion lines which have empty "Nome" and Tipo starts with
        # "Conversione di valuta generica".
        while i < n and not (rows[i].get("Nome") or "").strip():
            tipo = (rows[i].get("Tipo") or "").strip()
            if tipo.startswith("Conversione di valuta generica"):
                i += 1
                continue
            # Not a conversion line; leave for the next iteration
            break

    # Write output
    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=paypal_config["output_columns"])
        writer.writeheader()
        writer.writerows(out_rows)


if __name__ == "__main__":
    # For backward compatibility when run directly
    import argparse

    parser = argparse.ArgumentParser(description="Convert PayPal CSV to Firefly III import format.")
    parser.add_argument(
        "input",
        nargs="?",
        default=None,
        help="Input PayPal CSV path",
    )
    parser.add_argument(
        "output",
        nargs="?",
        default=None,
        help="Output CSV path for Firefly III import",
    )
    parser.add_argument("--config", default="config/config.json", help="Percorso file configurazione JSON")

    args = parser.parse_args()

    with open(args.config, 'r', encoding='utf-8') as f:
        config = json.load(f)

    paypal_config = config["paypal"]
    input_path = args.input or paypal_config["default_input"]
    output_path = args.output or paypal_config["default_output"]

    convert_paypal_csv_to_firefly(input_path, output_path, config)