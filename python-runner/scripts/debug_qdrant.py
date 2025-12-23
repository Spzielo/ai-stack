from qdrant_client import QdrantClient
import logging

client = QdrantClient(host="qdrant", port=6333)
print("Client type:", type(client))
print("Available attributes:")
print(dir(client))

try:
    print("Has search?", hasattr(client, 'search'))
except Exception as e:
    print(e)
