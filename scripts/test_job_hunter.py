import requests
import json

URL = "http://localhost:8001/analyze"

sample_offer = """
Recrutement: Senior AI Engineer @ TechStartup (Paris/Remote)
Nous cherchons un expert Python avec 5 ans d'expérience.
Missions: 
- Développer des agents IA.
- Optimiser le backend FastAPI.
Compétences: Python, Docker, NLP, Leadership.
Salaire: 80k-100k.
Contexte: Croissance rapide, nouvelle équipe.
"""

def test_analyze():
    print(f"Sending offer to {URL}...")
    try:
        payload = {"raw_text": sample_offer}
        response = requests.post(URL, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Success!")
            print(f"Role Detected: {data['offer_metadata']['role']}")
            print(f"Match Level: {data['match']['level']}")
            print(f"Score: {data['match']['total_score']}/100")
            print("\n--- Generated CV Excerpt ---")
            print(data['generated_content']['cv_markdown'][:200] + "...")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("Make sure the job-hunter service is running (docker-compose up -d job-hunter)")

if __name__ == "__main__":
    test_analyze()
