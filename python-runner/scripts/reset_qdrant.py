from core.vector import vector_store, COLLECTION_NAME
import logging

logging.basicConfig(level=logging.INFO)
print(f"🗑️ Deleting collection '{COLLECTION_NAME}'...")

try:
    vector_store._client.delete_collection(COLLECTION_NAME)
    print("✅ Collection deleted. Restart the service to recreate it with correct dimensions.")
except Exception as e:
    print(f"❌ Error: {e}")
