import logging
import sys
from core.vector import vector_store

logging.basicConfig(level=logging.INFO)

print("🧪 Testing Vector Store...")

# 1. Connection check (implicit in init)
if not vector_store._client:
    print("❌ Client initialization failed. Check logs.")
    sys.exit(1)

print("✅ Connected to Qdrant.")

# 2. Embedding check
text = "Hello Vector World"
print(f"embedding '{text}'...")
vec = vector_store._get_embedding(text)

if vec and len(vec) == 1536:
    print("✅ Embedding gen success (1536 dims).")
else:
    print("❌ Embedding failed.")
