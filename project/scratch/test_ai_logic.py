import os
import sys
import django

# Set up Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from ai_engine.services import generate_market_segmentation, classify_market_domain

def test_space_domain():
    market = "Orbital Transfer Vehicle Market"
    print(f"Testing market: {market}")
    
    # 1. Test Domain Classification
    domain = classify_market_domain(market)
    print(f"Detected Domain: {domain}")
    
    # 2. Test Segmentation Generation
    raw, detected_domain, meta = generate_market_segmentation(market)
    print("\n--- RAW AI OUTPUT ---")
    print(raw)
    print("\n--- METADATA ---")
    print(meta)

if __name__ == "__main__":
    test_space_domain()
