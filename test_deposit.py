#!/usr/bin/env python3
"""
Quick test to verify deposit_usdc.py can load and connect.
This doesn't execute transactions, just validates setup.
"""
import sys
from deposit_usdc import load_credentials, RPC_URL
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

try:
    # Test loading credentials
    print("Testing credential loading...")
    private_key, wallet_address = load_credentials()
    assert private_key and len(private_key) >= 64, "Invalid private key"
    assert wallet_address and wallet_address.startswith('0x'), "Invalid wallet address"
    print(f"✓ Credentials loaded: {wallet_address}")
    
    # Test Web3 connection
    print(f"\nTesting connection to {RPC_URL}...")
    web3 = Web3(Web3.HTTPProvider(RPC_URL))
    web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    
    if not web3.is_connected():
        raise Exception("Failed to connect to Polygon")
    
    print("✓ Connected to Polygon")
    
    # Test balance query
    balance = web3.eth.get_balance(wallet_address)
    print(f"✓ Balance query successful: {web3.from_wei(balance, 'ether')} MATIC")
    
    print("\n✅ All basic checks passed!")
    print("\nNext steps:")
    print("  - Ensure your wallet has MATIC for gas fees")
    print("  - Ensure your wallet has USDC for trading")
    print("  - Run: python deposit_usdc.py --check")
    print("  - Run: python deposit_usdc.py  (to set allowances)")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
