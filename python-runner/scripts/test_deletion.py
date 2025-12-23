from core.llm import llm_client # Ensure environment is set, though requests is better 
import requests
import json
import time

URL = "http://localhost:8000/v1/chat/completions"

def chat(text):
    print(f"\nUser: '{text}'")
    try:
        with requests.post(URL, json={"model": "test", "messages": [{"role": "user", "content": text}]}, stream=True) as r:
            for line in r.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    if decoded.startswith("data: ") and decoded != "data: [DONE]":
                        json_str = decoded[6:]
                        try:
                            chunk = json.loads(json_str)
                            content = chunk['choices'][0]['delta'].get('content', '')
                            print(content, end="", flush=True)
                        except: pass
        print()
    except Exception as e:
        print(f"Error: {e}")

print("🧪 Testing Deletion...")

# 1. Create
chat("Rappelle-moi d'acheter du jambon.")
chat("Note: Le mot de passe wifi est 'banana'.")
time.sleep(2)

# 2. Delete
chat("Supprime la tâche acheter du jambon.")
chat("Efface la note sur le wifi.")
