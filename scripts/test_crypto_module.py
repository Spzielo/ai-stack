#!/usr/bin/env python3
"""
Test script for Crypto One-Glance module.
Tests API endpoints with sample data.
"""

import requests
import json
from datetime import date

BASE_URL = "http://localhost:8000"

def test_dashboard():
    """Test dashboard endpoint."""
    print("🧪 Testing GET /crypto/dashboard...")
    response = requests.get(f"{BASE_URL}/crypto/dashboard")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Dashboard OK: {len(data['assets'])} assets")
        return True
    else:
        print(f"❌ Dashboard failed: {response.status_code}")
        return False


def test_asset_detail():
    """Test asset detail endpoint."""
    print("\n🧪 Testing GET /crypto/assets/AAVE...")
    response = requests.get(f"{BASE_URL}/crypto/assets/AAVE")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Asset detail OK: {data['symbol']} - {data['name']}")
        print(f"   Category: {data['category']}, Chain: {data['chain']}")
        return True
    else:
        print(f"❌ Asset detail failed: {response.status_code}")
        return False


def test_ingest_metrics():
    """Test metrics ingestion."""
    print("\n🧪 Testing POST /crypto/ingest/metrics...")
    
    payload = {
        "items": [
            {
                "symbol": "AAVE",
                "date": str(date.today()),
                "price_usd": 285.42,
                "market_cap": 4250000000,
                "volume_24h": 180000000,
                "tvl": 12500000000
            },
            {
                "symbol": "ETH",
                "date": str(date.today()),
                "price_usd": 3850.00,
                "market_cap": 462000000000,
                "volume_24h": 25000000000
            }
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/crypto/ingest/metrics",
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Metrics ingestion OK: {data['ingested']} ingested, {data['skipped']} skipped")
        return True
    else:
        print(f"❌ Metrics ingestion failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def test_compute_scores():
    """Test scoring computation."""
    print("\n🧪 Testing POST /crypto/compute/scores...")
    
    response = requests.post(f"{BASE_URL}/crypto/compute/scores")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Scoring OK: {data['computed']} scores computed")
        if data['status_changes']:
            print(f"   Status changes: {len(data['status_changes'])}")
            for change in data['status_changes'][:3]:
                print(f"   - {change['symbol']}: {change['from_status']} → {change['to_status']}")
        return True
    else:
        print(f"❌ Scoring failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def test_asset_metrics():
    """Test asset metrics endpoint."""
    print("\n🧪 Testing GET /crypto/assets/AAVE/metrics?range=30d...")
    
    response = requests.get(f"{BASE_URL}/crypto/assets/AAVE/metrics?range=30d")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Asset metrics OK: {len(data['metrics'])} data points")
        return True
    else:
        print(f"❌ Asset metrics failed: {response.status_code}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Crypto One-Glance Module - Test Suite")
    print("=" * 60)
    
    tests = [
        test_dashboard,
        test_asset_detail,
        test_ingest_metrics,
        test_compute_scores,
        test_asset_metrics,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
