import sys
import os

# Add project directory to python path
sys.path.append(r'c:\Users\Santosh\Desktop\market\project')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from ai_engine.services import generate_market_segmentation, parse_segmentation_response, validate_segmentation

print("Starting AI query...")
market = "Artificial Intelligence Software Market"
raw = generate_market_segmentation(market)
print(f"RAW Response:\n{raw}\n---")
parsed = parse_segmentation_response(raw)
validated = validate_segmentation(parsed)
print("VALIDATED JSON:")
import json
print(json.dumps(validated, indent=2))
