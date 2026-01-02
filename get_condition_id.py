#!/usr/bin/env python3
"""
Extract condition_id from a Polymarket URL.
Usage: python get_condition_id.py <polymarket_url>
"""
import sys
import re
import requests

def get_condition_id_from_url(url):
    """Extract condition_id from a Polymarket URL."""
    
    # Extract slug from URL
    # Format: https://polymarket.com/event/{slug}?tid={tid}
    match = re.search(r'/event/([^?]+)', url)
    if not match:
        print(f"❌ Could not extract slug from URL: {url}")
        return None
    
    slug = match.group(1)
    print(f"Extracted slug: {slug}")
    
    # Try Gamma API first
    gamma_url = f"https://gamma-api.polymarket.com/markets/{slug}"
    print(f"\nTrying Gamma API: {gamma_url}")
    
    try:
        response = requests.get(gamma_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            condition_id = data.get('conditionId')
            if condition_id:
                print(f"✓ Found via Gamma API!")
                print(f"\nCondition ID: {condition_id}")
                print(f"Question: {data.get('question')}")
                print(f"Active: {data.get('active')}")
                print(f"Closed: {data.get('closed')}")
                return condition_id
        else:
            print(f"✗ Gamma API returned {response.status_code}")
    except Exception as e:
        print(f"✗ Gamma API error: {e}")
    
    # Try CLOB API by scanning recent markets
    print(f"\nTrying CLOB API scan...")
    try:
        from py_clob_client.client import ClobClient
        from py_clob_client.constants import POLYGON
        import json
        
        # Load config for authentication
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        client = ClobClient(
            host="https://clob.polymarket.com",
            key=config['api_credentials']['private_key'],
            chain_id=POLYGON
        )
        
        # Scan first 1000 markets
        response = client.get_markets(next_cursor="")
        markets = response.get('data', []) if isinstance(response, dict) else response
        
        for market in markets[:1000]:
            if market.get('slug') == slug:
                condition_id = market.get('condition_id')
                print(f"✓ Found via CLOB API!")
                print(f"\nCondition ID: {condition_id}")
                print(f"Question: {market.get('question')}")
                print(f"Active: {market.get('active')}")
                return condition_id
        
        print(f"✗ Market not found in first 1000 CLOB markets")
        
    except Exception as e:
        print(f"✗ CLOB API error: {e}")
    
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python get_condition_id.py <polymarket_url>")
        print("\nExample:")
        print("  python get_condition_id.py 'https://polymarket.com/event/btc-updown-15m-1767389400?tid=1767390107469'")
        sys.exit(1)
    
    url = sys.argv[1]
    
    print("=" * 80)
    print(f"Extracting condition_id from URL:")
    print(f"{url}")
    print("=" * 80)
    
    condition_id = get_condition_id_from_url(url)
    
    if condition_id:
        print("\n" + "=" * 80)
        print("✅ SUCCESS!")
        print("\nTo use this market, add to your config.json:")
        print('  "market_settings": {')
        print('    ...')
        print(f'    "manual_condition_id": "{condition_id}"')
        print('  }')
        print("\nThen run: python main.py")
    else:
        print("\n" + "=" * 80)
        print("❌ Could not find condition_id for this market")
        print("\nThe market may be:")
        print("  - Too new or too old")
        print("  - Closed/inactive")
        print("  - Not indexed in either API")


if __name__ == '__main__':
    main()
