import requests
import json
import time

API_URL_CAPTURE = "http://localhost:8000/capture"
API_URL_RUN = "http://localhost:8000/run"

print("🧪 Testing RAG Flow...")

# 1. Ingest a "Secret" Note
secret = "The secret code for the vault is 998877."
print(f"1. Ingesting Note: '{secret}'")
resp = requests.post(API_URL_CAPTURE, json={"content": secret})
print(f"   Status: {resp.json().get('status')}")

# Wait for embedding (it's synchronous but good measure)
time.sleep(2)

# 2. Ask about it
question = "What is the secret code?"
print(f"2. Asking Chat: '{question}'")
resp = requests.post(API_URL_RUN, json={"text": question})
data = resp.json()

print("\n🤖 Answer:")
print(f"> {data.get('message')}")

print("\n📄 Sources:")
for s in data.get('sources', []):
    print(f"- {s.get('content')}")

if "998877" in data.get('message', ''):
    print("\n✅ RAG SUCCESS!")
else:
    print("\n❌ RAG FAILED.")
