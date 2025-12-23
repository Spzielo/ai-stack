import requests
import json
import sys

API_URL = "http://localhost:8000/capture"

def test_capture(text, expected_type):
    print(f"🧪 Testing input: '{text}' ...")
    try:
        response = requests.post(API_URL, json={"content": text})
        response.raise_for_status()
        data = response.json()
        
        print(f"   Status: {data.get('status')}")
        classification = data.get('classification', {})
        res_type = classification.get('type')
        res_confidence = classification.get('confidence')
        print(f"   Classified as: {res_type} (Confidence: {res_confidence})")
        
        if res_type == expected_type:
            print("   ✅ PASS")
        else:
            print(f"   ❌ FAIL (Expected {expected_type}, got {res_type})")
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")

print("--- E2E Classification Test ---")

# Test 1: Task
test_capture("Remember to buy milk tomorrow", "task")

# Test 2: Note
test_capture("Idea for a new app: Tinder for cats.", "note")

# Test 3: Project (maybe?)
test_capture("Plan a trip to Japan including flights and hotels", "project")

print("-------------------------------")
