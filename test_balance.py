#!/usr/bin/env python3
"""
Test script to debug the balance API response structure.
"""
import json
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import BalanceAllowanceParams, AssetType
from py_clob_client.constants import POLYGON

# Load the real config
with open('config.json', 'r') as f:
    config = json.load(f)

try:
    # Initialize client with real credentials
    client = ClobClient(
        host="https://clob.polymarket.com",
        key=config['api_credentials']['private_key'],
        chain_id=POLYGON
    )
    
    print("✓ Client initialized")
    
    # Authenticate
    client.assert_level_1_auth()
    print("✓ Level 1 auth successful")
    
    api_creds = client.create_or_derive_api_creds()
    client.set_api_creds(api_creds)
    print("✓ Level 2 auth successful")
    
    # Try getting balance
    print("\nFetching balance_allowance...")
    params = BalanceAllowanceParams(asset_type=AssetType.COLLATERAL)
    response = client.get_balance_allowance(params=params)
    
    print(f"\nResponse type: {type(response)}")
    print(f"Response: {response}")
    
    if isinstance(response, dict):
        print(f"\nAvailable keys: {list(response.keys())}")
        for key in response:
            print(f"  - {key}: {response[key]}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
