#!/usr/bin/env python3
"""
Debug Gamma API response to see exact market format.
"""
import requests
import json

GAMMA_API_URL = "https://gamma-api.polymarket.com"

print("Fetching markets from Gamma API...\n")
print("=" * 100)

try:
    url = f"{GAMMA_API_URL}/markets"
    params = {
        'active': 'true',
        'closed': 'false',
        'limit': 100
    }
    
    response = requests.get(url, params=params, timeout=10)
    
    if response.status_code != 200:
        print(f"Error: API returned status {response.status_code}")
        print(response.text)
        exit(1)
    
    markets = response.json()
    
    print(f"✓ Retrieved {len(markets)} markets\n")
    print("=" * 100)
    
    # Find BTC-related markets
    btc_markets = []
    for market in markets:
        title = market.get('question', '').lower()
        
        if 'btc' in title or 'bitcoin' in title:
            btc_markets.append(market)
    
    print(f"\n📊 Found {len(btc_markets)} BTC-related markets:\n")
    print("-" * 100)
    
    for i, market in enumerate(btc_markets, 1):
        print(f"\n{i}. {market.get('question')}")
        print(f"   Slug: {market.get('slug', 'N/A')}")
        print(f"   Condition ID: {market.get('conditionId', 'N/A')}")
        print(f"   Active: {market.get('active')}")
        print(f"   Closed: {market.get('closed')}")
        print(f"   End Date: {market.get('endDate', 'N/A')}")
        print(f"   Outcomes: {market.get('outcomes', [])}")
        print(f"   Description: {market.get('description', '')[:100]}...")
        
        # Show first market's full structure
        if i == 1:
            print(f"\n   Full structure of first BTC market:")
            print(f"   {json.dumps(market, indent=4)}")
    
    if not btc_markets:
        print("\n❌ No BTC markets found in first 100 active markets")
        print("\nShowing first 10 markets for reference:")
        for i, market in enumerate(markets[:10], 1):
            print(f"\n{i}. {market.get('question')}")
            print(f"   Slug: {market.get('slug', 'N/A')}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
