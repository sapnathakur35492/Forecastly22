import os
import sys
import django

# Set up Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from ai_engine.services import professionalize_market_title, classify_market_domain

def test_titles():
    test_cases = [
        "santosh",
        "12345 market",
        "asdfghjkl",
        "xsfs",
        "OTV",
        "Electric vehicle",
        "Satellite logistics",
        "242",
        "ssdfg"
    ]
    
    print(f"{'Input':<25} | {'Detected Domain':<15} | {'Professional Title'}")
    print("-" * 80)
    
    for tc in test_cases:
        domain = classify_market_domain(tc)
        prof_title = professionalize_market_title(tc, domain)
        print(f"{tc:<25} | {domain:<15} | {prof_title}")

if __name__ == "__main__":
    test_titles()
