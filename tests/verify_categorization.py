import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from converters.paypal import _categorize_transaction

test_cases = [
    ("Payment to ebay", "ebay", ""),
    ("Purchase from 39euroglasses", "lenti a contatto", ""),
    ("ADRIAL payment", "lenti a contatto", ""),
    ("BBB S.p.A. invoice", "Clothing", ""),
    ("Bergfreunde shop", "Clothing", ""),
    ("Capri srl store", "Clothing", ""),
    ("Colella Group srl", "Clothing", ""),
    ("Converse Netherlands BV", "Clothing", ""),
    ("Dagsmejan sleepwear", "Clothing", ""),
    ("DEPORVILLAGE sports", "Clothing", ""),
    ("Farfetch UK Ltd.", "Clothing", ""),
    ("FC-Moto gear", "Clothing", ""),
    ("H & M Hennes & Mauritz SRL", "Clothing", ""),
    ("KREUZBERGKINDER GMBH", "Clothing", ""),
    ("Louis Vuitton Italia Srl", "Clothing", ""),
    ("Maltese Lab srl", "Clothing", ""),
    ("Booking.com BV hotel", "Travel", ""),
    ("Deliveroo food", "Supermarkets and food", ""),
    ("Euro Company srl", "Supermarkets and food", ""),
    ("Eurochef Italia Spa", "Supermarkets and food", ""),
    ("Madi Ventura S.p.A", "Supermarkets and food", ""),
    ("EasyPark Italia Srl parking", "Parking", ""),
    ("farmacia centrale", "Prodotti farmacia e parafarmacia", ""),
    ("farmacie comunali", "Prodotti farmacia e parafarmacia", ""),
    ("Google Services", "Servizi Google", ""),
    ("Microsoft Payments", "Servizi Microsoft", ""),
    ("MoonPay crypto", "Crypto", ""),
    ("NESPRESSO coffee", "Supermarkets and food", ""),
    ("NETFLIX subscription", "Entertainment", ""),
    ("Notino cosmetics", "Personal care", ""),
    ("Parkvia parking", "Parking", ""),
    ("Sisal bet", "Scommesse", ""),
    ("Sky Italia tv", "Entertainment", ""),
    ("Spotify music", "Entertainment", ""),
    ("Temu shop", "Temu", ""),
    ("TIKR terminal", "Financial Data", ""),
    ("TLD Registrar domain", "Domain Names", ""),
    ("Namecheap domain", "Domain Names", ""),
    ("TRADEINN sports", "Clothing", ""),
    ("Unicorn Data Services", "Financial Data", ""),
    ("YOOX fashion", "Clothing", ""),
    ("Zalando shoes", "Clothing", ""),
    ("Unknown Merchant", "", "to_categorize"),
]

def run_tests():
    failed = 0
    for name, expected_category, expected_tags in test_cases:
        category, tags = _categorize_transaction(name)
        if category != expected_category or tags != expected_tags:
            print(f"FAIL: '{name}' -> Expected ({expected_category}, {expected_tags}), got ({category}, {tags})")
            failed += 1
        else:
            # print(f"PASS: '{name}'")
            pass
    
    if failed == 0:
        print("All tests passed!")
    else:
        print(f"{failed} tests failed.")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
