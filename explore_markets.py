#!/usr/bin/env python3
"""
Explore available Bitcoin markets on Polymarket.
"""
import json
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

print("Searching for Bitcoin-related markets...\n")
print("=" * 100)

bitcoin_markets = []
next_cursor = ""
scanned = 0
max_scan = 10000  # Limit scan to first 10k markets

while scanned < max_scan:
    response = client.get_markets(next_cursor=next_cursor)
    
    if isinstance(response, dict):
        markets = response.get('data', [])
        next_cursor = response.get('next_cursor', "")
    elif isinstance(response, list):
        markets = response
        next_cursor = ""
    else:
        break
    
    if not markets:
        break
    
    scanned += len(markets)
    
    for market in markets:
        if not isinstance(market, dict):
            continue
        
        title = market.get('question', '').lower()
        
        # Find any Bitcoin-related market
        if 'bitcoin' in title or 'btc' in title:
            tokens = market.get('tokens', [])
            active = market.get('active', False)
            end_date = market.get('end_date_iso', 'N/A')
            
            bitcoin_markets.append({
                'title': market.get('question'),
                'id': market.get('condition_id'),
                'active': active,
                'end_date': end_date,
                'tokens': [t.get('outcome') for t in tokens]
            })
    
    if not next_cursor or next_cursor == "0":
        break
    
    print(f"Scanned {scanned} markets, found {len(bitcoin_markets)} Bitcoin markets...", end='\r')

print(f"\n\nFound {len(bitcoin_markets)} Bitcoin-related markets (scanned {scanned} total markets)")
print("=" * 100)

# Group by active status
active_markets = [m for m in bitcoin_markets if m['active']]
inactive_markets = [m for m in bitcoin_markets if not m['active']]

print(f"\n📊 ACTIVE Bitcoin markets ({len(active_markets)}):")
print("-" * 100)
for i, market in enumerate(active_markets[:20], 1):  # Show first 20
    tokens = ', '.join(market['tokens'][:3])  # Show first 3 tokens
    print(f"{i}. {market['title'][:70]}")
    print(f"   ID: {market['id']}")
    print(f"   Tokens: {tokens}")
    print(f"   Ends: {market['end_date'][:19] if market['end_date'] != 'N/A' else 'N/A'}")
    print()

if len(active_markets) > 20:
    print(f"   ... and {len(active_markets) - 20} more active markets")

print(f"\n📊 INACTIVE Bitcoin markets ({len(inactive_markets)}) - showing first 10:")
print("-" * 100)
for i, market in enumerate(inactive_markets[:10], 1):
    tokens = ', '.join(market['tokens'][:3])
    print(f"{i}. {market['title'][:70]}")
    print(f"   Tokens: {tokens}")
    print()

# Look specifically for time-based markets
print("\n🔍 Time-based Bitcoin markets (minute/hour/day):")
print("-" * 100)
time_based = [m for m in bitcoin_markets if any(word in m['title'].lower() for word in ['minute', 'min', 'hour', 'day', 'next'])]
for market in time_based[:10]:
    status = "✓ ACTIVE" if market['active'] else "✗ Inactive"
    print(f"{status} | {market['title']}")
    print(f"         Tokens: {', '.join(market['tokens'])}")
    print()

if not time_based:
    print("❌ No time-based Bitcoin markets found")

print("\n" + "=" * 100)
print("\n💡 Suggestions:")
if active_markets:
    print(f"✓ Found {len(active_markets)} active Bitcoin markets")
    print("  You can modify the bot to trade on one of these markets instead")
else:
    print("❌ No active Bitcoin markets found")
    print("  Bitcoin 15min markets may not exist anymore on Polymarket")
    print("  Consider:")
    print("    1. Check polymarket.com manually for available markets")
    print("    2. Modify the bot to trade on different prediction markets")
    print("    3. Wait for new Bitcoin markets to be created")
