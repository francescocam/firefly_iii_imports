from __future__ import annotations

import csv
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
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
) -> List[Dict[str, str]]:
    """Convert PayPal CSV to Firefly III import format."""
    try:
        paypal_config = config["paypal"]
    except KeyError as exc:
        raise ValueError("Missing 'paypal' section in configuration.") from exc

    required_keys = [
        "source_account",
        "output_columns",
        "default_input",
        "default_output",
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
    orphan_rows: List[Dict[str, str]] = []

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
            orphan_rows.append({"row_number": i + 1, "name": name})
            break
        row2 = rows[i + 1]

        # If the next row also has a "Nome", it is another header – record orphan
        if (row2.get("Nome") or "").strip():
            orphan_rows.append({"row_number": i + 1, "name": name})
            i += 1
            continue

        # Extract fields from the second row as per spec
        date_str = (row2.get("Data") or "").strip()
        currency = (row2.get("Valuta") or "").strip()
        amount_raw = (row2.get("Importo") or "").strip()
        amount_val = _parse_decimal_it(amount_raw)

        # Business rule from user: positive amount -> withdrawal, else deposit
        if positive_is_withdrawal:
            tx_type = "withdrawal" if amount_val > 0 else "deposit"
        else:
            tx_type = "deposit" if amount_val > 0 else "withdrawal"

        amount_out = (-amount_val).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)

        out_rows.append(
            {
                "date": date_str,
                "description": name,
                "amount": format(amount_out, "f"),
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
        writer = csv.DictWriter(f, fieldnames=output_columns)
        writer.writeheader()
        writer.writerows(out_rows)

    return orphan_rows


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

    orphans = convert_paypal_csv_to_firefly(input_path, output_path, config)
    if orphans:
        printable = ", ".join(
            f"row {entry['row_number']}: {entry['name']}" for entry in orphans
        )
        print(
            "Skipped unpaired PayPal rows – review CSV near " + printable,
            flush=True,
        )
