import sys
import logging
from core.llm import llm_client
from core.models import ClassificationResult

logging.basicConfig(level=logging.INFO)

if not llm_client.is_ready():
    print("❌ LLM not configured.")
    sys.exit(1)

print("🧠 Testing LLM Classification...")
text = "Remember to buy milk tomorrow"
print(f"Input: '{text}'")

result = llm_client.classify(text, ClassificationResult)

if result:
    print("\n✅ Classification Successful!")
    print(result.model_dump_json(indent=2))
else:
    print("\n❌ Classification Failed.")
