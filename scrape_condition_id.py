#!/usr/bin/env python3
"""
Extract condition_id by scraping the Polymarket web page.
"""
import sys
import re
import requests
from bs4 import BeautifulSoup

def scrape_condition_id(url):
    """Scrape condition_id from Polymarket page."""
    print(f"Fetching page: {url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"✗ HTTP {response.status_code}")
            return None
        
        html = response.text
        
        # Method 1: Look for condition_id in script tags
        pattern1 = r'"conditionId"\s*:\s*"(0x[a-fA-F0-9]{64})"'
        matches = re.findall(pattern1, html)
        if matches:
            condition_id = matches[0]
            print(f"✓ Found via pattern matching!")
            return condition_id
        
        # Method 2: Look for condition_id in any format
        pattern2 = r'(0x[a-fA-F0-9]{64})'
        matches = re.findall(pattern2, html)
        if matches:
            # Get unique matches
            unique = list(set(matches))
            if len(unique) == 1:
                condition_id = unique[0]
                print(f"✓ Found unique condition_id!")
                return condition_id
            elif len(unique) > 1:
                print(f"⚠️  Found {len(unique)} potential condition_ids:")
                for i, cid in enumerate(unique, 1):
                    print(f"  {i}. {cid}")
                print("\n  Using the first one (most likely correct)")
                return unique[0]
        
        # Method 3: Parse as JSON embedded in page
        json_pattern = r'<script[^>]*>.*?({.*?"conditionId".*?})</script>'
        json_matches = re.findall(json_pattern, html, re.DOTALL)
        for json_str in json_matches:
            try:
                import json
                data = json.loads(json_str)
                if 'conditionId' in data:
                    condition_id = data['conditionId']
                    print(f"✓ Found in JSON data!")
                    return condition_id
            except:
                continue
        
        print("✗ Could not find condition_id in page HTML")
        return None
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python scrape_condition_id.py <polymarket_url>")
        print("\nExample:")
        print("  python scrape_condition_id.py 'https://polymarket.com/event/btc-updown-15m-1767389400'")
        sys.exit(1)
    
    url = sys.argv[1]
    
    print("=" * 80)
    print("Scraping condition_id from Polymarket page")
    print("=" * 80)
    
    condition_id = scrape_condition_id(url)
    
    if condition_id:
        print("\n" + "=" * 80)
        print("✅ SUCCESS!")
        print(f"\nCondition ID: {condition_id}")
        print("\nTo use this market, edit config.json:")
        print('  "market_settings": {')
        print('    ...')
        print(f'    "manual_condition_id": "{condition_id}"')
        print('  }')
        print("\nThen run: python main.py")
    else:
        print("\n" + "=" * 80)
        print("❌ Could not extract condition_id from page")
        print("\nTry:")
        print("  1. Check if the URL is correct")
        print("  2. Check if the market is still active")
        print("  3. Inspect the page source manually in a browser")


if __name__ == '__main__':
    main()
