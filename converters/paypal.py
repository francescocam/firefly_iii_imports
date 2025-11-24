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


def _categorize_transaction(name: str) -> tuple[str, str]:
    """
    Categorize transaction based on the payee name.

    Args:
        name: The name of the payee/description.

    Returns:
        A tuple containing (category, tags).
    """
    category = ""
    tags = ""
    
    # Case-insensitive matching as requested.
    name_lower = name.lower()
    
    if "ebay" in name_lower:
        category = "ebay"
    elif "39euroglasses" in name_lower:
        category = "lenti a contatto"
    elif "adrial" in name_lower:
        category = "lenti a contatto"
    elif "bbb s.p.a." in name_lower:
        category = "Clothing"
    elif "bergfreunde" in name_lower:
        category = "Clothing"
    elif "capri srl" in name_lower:
        category = "Clothing"
    elif "colella group srl" in name_lower:
        category = "Clothing"
    elif "converse netherlands bv" in name_lower:
        category = "Clothing"
    elif "dagsmejan" in name_lower:
        category = "Clothing"
    elif "deporvillage" in name_lower:
        category = "Clothing"
    elif "farfetch uk ltd." in name_lower:
        category = "Clothing"
    elif "fc-moto" in name_lower:
        category = "Clothing"
    elif "h & m hennes & mauritz srl" in name_lower:
        category = "Clothing"
    elif "kreuzbergkinder gmbh" in name_lower:
        category = "Clothing"
    elif "louis vuitton italia srl" in name_lower:
        category = "Clothing"
    elif "maltese lab srl" in name_lower:
        category = "Clothing"
    elif "booking.com bv" in name_lower:
        category = "Travel"
    elif "deliveroo" in name_lower:
        category = "Supermarkets and food"
    elif "euro company srl" in name_lower:
        category = "Supermarkets and food"
    elif "eurochef italia spa" in name_lower:
        category = "Supermarkets and food"
    elif "madi ventura s.p.a" in name_lower:
        category = "Supermarkets and food"
    elif "easypark italia srl" in name_lower:
        category = "Parking"
    elif "farmacia" in name_lower:
        category = "Prodotti farmacia e parafarmacia"
    elif "farmacie" in name_lower:
        category = "Prodotti farmacia e parafarmacia"
    elif "google" in name_lower:
        category = "Servizi Google"
    elif "microsoft payments" in name_lower:
        category = "Servizi Microsoft"
    elif "moonpay" in name_lower:
        category = "Crypto"
    elif "nespresso" in name_lower:
        category = "Supermarkets and food"
    elif "netflix" in name_lower:
        category = "Entertainment"
    elif "notino" in name_lower:
        category = "Personal care"
    elif "parkvia" in name_lower:
        category = "Parking"
    elif "sisal" in name_lower:
        category = "Scommesse"
    elif "sky italia" in name_lower:
        category = "Entertainment"
    elif "spotify" in name_lower:
        category = "Entertainment"
    elif "temu" in name_lower:
        category = "Temu"
    elif "tikr" in name_lower:
        category = "Financial Data"
    elif "tld registrar" in name_lower:
        category = "Domain Names"
    elif "namecheap" in name_lower:
        category = "Domain Names"
    elif "tradeinn" in name_lower:
        category = "Clothing"
    elif "unicorn data services" in name_lower:
        category = "Financial Data"
    elif "yoox" in name_lower:
        category = "Clothing"
    elif "zalando" in name_lower:
        category = "Clothing"
    else:
        category = ""
        tags = "to_categorize"
        
    return category, tags


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

    output_columns = list(paypal_config["output_columns"])
    if not isinstance(output_columns, list) or not output_columns:
        raise ValueError("'paypal.output_columns' must be a non-empty list.")

    # Ensure category and tags are in output_columns
    if "category" not in output_columns:
        output_columns.append("category")
    if "tags" not in output_columns:
        output_columns.append("tags")

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

        # Categorize transaction
        category, tags = _categorize_transaction(name)

        # Create output row in Firefly III format
        out_rows.append(
            {
                "date_transaction": date_str,
                "description": name,
                "amount": format(amount_out, "f"),
                "account-name": paypal_config["source_account"],
                "opposing-name": name,
                "category": category,
                "tags": tags,
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
