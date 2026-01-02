#!/usr/bin/env python3
"""
Fetch details of a specific market from its slug.
"""
import json
import sys
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON

# The slug from the URL
SLUG = "btc-updown-15m-1767389400"

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

# Initialize client
client = ClobClient(
    host="https://clob.polymarket.com",
    key=config['api_credentials']['private_key'],
    chain_id=POLYGON
)

print(f"Fetching market with slug: {SLUG}\n")
print("=" * 80)

try:
    # Search for markets with this slug
    next_cursor = ""
    found = False
    scanned = 0
    max_scan = 20000
    
    while scanned < max_scan and not found:
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
            
            market_slug = market.get('slug', '')
            title = market.get('question', '')
            
            # Check if this is a BTC 15min market
            if 'btc' in market_slug.lower() or 'btc' in title.lower():
                if '15m' in market_slug or '15m' in title.lower():
                    print(f"\n✓ FOUND Bitcoin 15min market!")
                    print(f"  Title: {title}")
                    print(f"  Slug: {market_slug}")
                    print(f"  Condition ID: {market.get('condition_id')}")
                    print(f"  Active: {market.get('active')}")
                    print(f"  End Date: {market.get('end_date_iso')}")
                    
                    tokens = market.get('tokens', [])
                    print(f"\n  Tokens ({len(tokens)}):")
                    for token in tokens:
                        print(f"    - {token.get('outcome')}: {token.get('token_id')}")
                        print(f"      Price: ${token.get('price', 0)}")
                    
                    print(f"\n  Full market data:")
                    print(json.dumps(market, indent=2))
                    
                    found = True
                    break
        
        if not next_cursor or next_cursor == "0":
            break
        
        print(f"Scanned {scanned} markets...", end='\r')
    
    if not found:
        print(f"\n❌ Market not found after scanning {scanned} markets")
        print("\nTrying alternative search patterns...")
        
        # Try searching for any BTC markets
        print("\nAll BTC-related market slugs found:")
        next_cursor = ""
        scanned = 0
        btc_markets = []
        
        while scanned < 5000:
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
                slug = market.get('slug', '').lower()
                
                if 'btc' in slug or 'bitcoin' in title:
                    active = "✓" if market.get('active') else "✗"
                    btc_markets.append((active, slug, title[:60]))
            
            if not next_cursor or next_cursor == "0":
                break
        
        print(f"\nFound {len(btc_markets)} BTC markets:")
        for status, slug, title in btc_markets[:20]:
            print(f"{status} {slug}")
            print(f"   {title}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
