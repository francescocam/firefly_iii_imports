import pandas as pd
import pytest
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from converters.fineco import prepare_fineco_csv

def test_fineco_rules(tmp_path):
    # Create dummy input Excel
    data = {
        "Data_Valuta": ["01/01/2023", "02/01/2023", "03/01/2023", "04/01/2023"],
        "Descrizione": ["Trans1", "Trans2", "Trans3", "Trans4"],
        "Entrate": [100, 0, 0, 0],
        "Uscite": [0, 50, 20, 10],
        "Descrizione_Completa": [
            "Pagamento OBI VENEZIA 123",
            "Addebito imposta di bollo Dossier: 139284",
            "Unknown Transaction",
            "AMAZON IT"
        ]
    }
    df = pd.DataFrame(data)
    input_path = tmp_path / "input.xlsx"
    df.to_excel(input_path, index=False)

    output_path = tmp_path / "output.csv"

    config = {
        "fineco": {
            "fineco_account": "Fineco Account",
            "header_row": 0,
            "required_columns": ["Data_Valuta", "Descrizione", "Entrate", "Uscite", "Descrizione_Completa"],
            "currency_code": "EUR",
            "card_a": {"number": "9999", "source_account_name": "fineco carta prepagata"},
            "card_b": {"number": "8888", "source_account_name": "fineco carta credito"}
        }
    }

    # Run conversion
    prepare_fineco_csv(input_path, output_path, config)

    # Check output
    out = pd.read_csv(output_path)
    
    # Rule 1: OBI VENEZIA -> OBI, DIY
    row0 = out.iloc[0]
    assert row0["opposing-name"] == "OBI"
    assert row0["category"] == "DIY"

    # Rule 2: Addebito imposta di bollo Dossier: 139284 -> ...
    row1 = out.iloc[1]
    assert row1["opposing-name"] == "Addebito imposta di bollo Dossier: 139284"
    assert row1["category"] == "Taxes on Investments"

    # Rule 3: Unknown -> to_input, undefined
    row2 = out.iloc[2]
    assert row2["opposing-name"] == "to_input"
    assert row2["category"] == "undefined"

    # Rule 4: AMAZON -> Amazone, Amazone
    row3 = out.iloc[3]
    assert row3["opposing-name"] == "Amazone"
    assert row3["category"] == "Amazone"

if __name__ == "__main__":
    # Manually run the test function if executed directly
    from pathlib import Path
    import shutil
    
    tmp_dir = Path("tmp_test_fineco")
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir()
    
    try:
        test_fineco_rules(tmp_dir)
        print("Test passed!")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
