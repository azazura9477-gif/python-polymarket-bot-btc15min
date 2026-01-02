#!/usr/bin/env python3
"""
Search for BTC 15min markets using different API approaches.
"""
import json
import requests
import time
from datetime import datetime
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

# Initialize client
client = ClobClient(
    host="https://clob.polymarket.com",
    key=config['api_credentials']['private_key'],
    chain_id=POLYGON
)

print("Searching for BTC 15min markets using multiple methods...\n")
print("=" * 80)

# Method 1: Direct API search with slug pattern
print("\n🔍 Method 1: Searching via Polymarket API with slug pattern...")
try:
    # Try direct HTTP request to Polymarket's API
    url = "https://clob.polymarket.com/markets"
    
    # Try searching for active markets only
    response = requests.get(url, params={'active': 'true', 'limit': 1000}, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        markets = data if isinstance(data, list) else data.get('data', [])
        
        btc_15m_markets = []
        for market in markets:
            slug = market.get('slug', '').lower()
            title = market.get('question', '').lower()
            
            if ('btc' in slug or 'bitcoin' in title) and '15m' in slug:
                btc_15m_markets.append(market)
                print(f"\n✓ Found: {market.get('question')}")
                print(f"  Slug: {slug}")
                print(f"  ID: {market.get('condition_id')}")
                print(f"  Active: {market.get('active')}")
        
        print(f"\n  Total BTC 15m markets found: {len(btc_15m_markets)}")
    else:
        print(f"  ✗ API returned status {response.status_code}")
        
except Exception as e:
    print(f"  ✗ Error: {e}")

# Method 2: Check for recent/newest markets
print("\n🔍 Method 2: Checking most recent markets (last 1000)...")
try:
    # Get markets without cursor (should get newest)
    response = client.get_markets(next_cursor="")
    
    if isinstance(response, dict):
        markets = response.get('data', [])
    elif isinstance(response, list):
        markets = response
    else:
        markets = []
    
    btc_recent = []
    for market in markets[:1000]:
        if not isinstance(market, dict):
            continue
        
        slug = market.get('slug', '').lower()
        title = market.get('question', '').lower()
        
        if 'btc' in slug and '15m' in slug:
            btc_recent.append(market)
            print(f"\n✓ Found: {market.get('question')}")
            print(f"  Slug: {slug}")
            print(f"  ID: {market.get('condition_id')}")
            print(f"  End: {market.get('end_date_iso')}")
    
    print(f"\n  Total recent BTC 15m markets: {len(btc_recent)}")
    
except Exception as e:
    print(f"  ✗ Error: {e}")

# Method 3: Generate likely current slug based on timestamp
print("\n🔍 Method 3: Generating likely current market slugs...")
try:
    # Current timestamp and next 15min windows
    now = int(time.time())
    
    # Round to next 15min intervals
    intervals = []
    for i in range(0, 4):  # Check next hour (4 x 15min)
        ts = now + (i * 15 * 60)
        # Round to nearest 15min
        ts = (ts // (15 * 60)) * (15 * 60)
        intervals.append(ts)
    
    print(f"\n  Current time: {datetime.fromtimestamp(now)}")
    print(f"\n  Checking these likely timestamps:")
    
    for ts in intervals:
        slug = f"btc-updown-15m-{ts}"
        dt = datetime.fromtimestamp(ts)
        print(f"    • {slug} (ends at {dt})")
    
    # Try to fetch by condition_id derived from slug
    # Note: We can't easily get condition_id without the full market data
    
except Exception as e:
    print(f"  ✗ Error: {e}")

# Method 4: Search in events/collections
print("\n🔍 Method 4: Looking for BTC event collections...")
try:
    # Polymarket groups markets into events/collections
    # Try gamma markets API endpoint
    url = "https://gamma-api.polymarket.com/markets"
    
    response = requests.get(url, params={'active': True, 'limit': 100}, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        
        btc_gamma = []
        for market in data:
            title = market.get('question', '').lower()
            if 'btc' in title or 'bitcoin' in title:
                if '15' in title or 'minute' in title:
                    btc_gamma.append(market)
                    print(f"\n✓ Found: {market.get('question')}")
                    print(f"  Condition ID: {market.get('conditionId')}")
        
        print(f"\n  Total from Gamma API: {len(btc_gamma)}")
    else:
        print(f"  ✗ Gamma API returned status {response.status_code}")
        
except Exception as e:
    print(f"  ✗ Error: {e}")

print("\n" + "=" * 80)
print("\n💡 CONCLUSION:")
print("BTC 15min markets are likely:")
print("  1. Very short-lived (only active for 15 minutes)")
print("  2. Created continuously (new one every few minutes)")
print("  3. May require direct slug/condition_id lookup rather than scanning")
print("  4. Might not appear in standard market listings due to short duration")
print("\n📝 RECOMMENDATION:")
print("  Instead of scanning all markets, the bot should:")
print("  • Use a known pattern: btc-updown-15m-{timestamp}")
print("  • Generate likely timestamps (next 15min windows)")
print("  • Try to fetch each market directly by predicted slug/ID")
print("  • Or monitor Polymarket's websocket/events for new BTC markets")
