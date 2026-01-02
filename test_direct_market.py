#!/usr/bin/env python3
"""
Test direct access to the specific BTC 15min market.
"""
import requests
import json

# The timestamp from your URL: https://polymarket.com/event/btc-updown-15m-1767389400
TIMESTAMP = 1767389400
SLUG = f"btc-updown-15m-{TIMESTAMP}"

GAMMA_API = "https://gamma-api.polymarket.com"

print(f"Testing direct access to market: {SLUG}\n")
print("=" * 80)

# Test 1: Gamma API by slug
print("\n🔍 Test 1: Gamma API - Get market by slug")
print(f"URL: {GAMMA_API}/markets/{SLUG}")

try:
    response = requests.get(f"{GAMMA_API}/markets/{SLUG}", timeout=10)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✓ SUCCESS - Market found!")
        print(f"\nQuestion: {data.get('question')}")
        print(f"Condition ID: {data.get('conditionId')}")
        print(f"Active: {data.get('active')}")
        print(f"Closed: {data.get('closed')}")
        print(f"Outcomes: {data.get('outcomes')}")
        print(f"End Date: {data.get('endDate')}")
        print(f"\nFull data:\n{json.dumps(data, indent=2)}")
    else:
        print(f"✗ FAILED - {response.text[:200]}")
except Exception as e:
    print(f"✗ ERROR: {e}")

# Test 2: Try variations of the slug
print("\n\n🔍 Test 2: Trying slug variations")
variations = [
    f"btc-updown-15m-{TIMESTAMP}",
    f"btc-up-down-15m-{TIMESTAMP}",
    f"bitcoin-updown-15m-{TIMESTAMP}",
    f"btc-15m-{TIMESTAMP}",
]

for slug_var in variations:
    try:
        response = requests.get(f"{GAMMA_API}/markets/{slug_var}", timeout=5)
        if response.status_code == 200:
            print(f"✓ Found with slug: {slug_var}")
            data = response.json()
            print(f"  Question: {data.get('question')}")
            break
        else:
            print(f"✗ Not found: {slug_var} (status {response.status_code})")
    except Exception as e:
        print(f"✗ Error with {slug_var}: {e}")

# Test 3: Search in events API
print("\n\n🔍 Test 3: Check events/collections API")
try:
    response = requests.get(f"{GAMMA_API}/events", params={'archived': 'false'}, timeout=10)
    if response.status_code == 200:
        events = response.json()
        print(f"Retrieved {len(events)} events")
        
        btc_events = [e for e in events if 'btc' in e.get('slug', '').lower() or 'bitcoin' in e.get('title', '').lower()]
        print(f"Found {len(btc_events)} BTC-related events")
        
        for event in btc_events[:5]:
            print(f"  - {event.get('slug')}: {event.get('title')}")
    else:
        print(f"Events API returned {response.status_code}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 80)
print("\n💡 CONCLUSION:")
print("If Gamma API doesn't return these markets, they might be:")
print("  1. Only accessible via CLOB API (not Gamma)")
print("  2. In a different event/collection structure")
print("  3. Using a different slug format")
print("  4. Not indexed in Gamma API due to short lifetime")
