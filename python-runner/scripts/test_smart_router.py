import requests
import json

URL = "http://localhost:8000/v1/chat/completions"

def chat(text):
    print(f"\nUser: '{text}'")
    resp = requests.post(URL, json={
        "model": "smart-router",
        "messages": [{"role": "user", "content": text}]
    })
    
    if resp.status_code != 200:
        print(f"Error: {resp.text}")
        return

    content = resp.json()["choices"][0]["message"]["content"]
    print(f"Bot: {content}")

print("🧪 Testing Smart Router...")

# 0. Seed Data (Since we reset DB)
chat("Note: The secret code of the vault is 998877.")

import time
time.sleep(2) # Wait for vector sync/indexing

# 1. Test Capture (Write)
chat("Rappelle-moi d'acheter du lait demain.")

# 2. Test Question (Read)
chat("Quel est le code secret du coffre ?")

# 3. Test Chat (Casual)
chat("Bonjour, comment vas-tu ?")
