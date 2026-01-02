#!/usr/bin/env python3
"""
Network diagnostic script to test connectivity to Polygon RPCs.
"""
import sys
import time
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

RPC_URLS = [
    'https://polygon-rpc.com',
    'https://polygon.llamarpc.com',
    'https://rpc-mainnet.matic.network',
    'https://rpc-mainnet.maticvigil.com',
    'https://polygon-bor-rpc.publicnode.com',
    'https://polygon.drpc.org',
    'https://1rpc.io/matic',
]

print("Testing Polygon RPC endpoints...\n")
print("=" * 80)

working_rpcs = []
failed_rpcs = []

for i, rpc_url in enumerate(RPC_URLS, 1):
    print(f"\n{i}/{len(RPC_URLS)} Testing: {rpc_url}")
    print("-" * 80)
    
    start_time = time.time()
    
    try:
        # Test connection
        web3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 15}))
        web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        
        # Check if connected
        if not web3.is_connected():
            print("✗ Failed to connect")
            failed_rpcs.append((rpc_url, "Not connected"))
            continue
        
        # Get chain ID
        chain_id = web3.eth.chain_id
        
        # Get latest block
        block_number = web3.eth.block_number
        
        # Get gas price
        gas_price = web3.eth.gas_price
        gas_price_gwei = web3.from_wei(gas_price, 'gwei')
        
        elapsed = time.time() - start_time
        
        print(f"✓ Connected successfully!")
        print(f"  Chain ID: {chain_id}")
        print(f"  Block: {block_number:,}")
        print(f"  Gas Price: {gas_price_gwei:.2f} gwei")
        print(f"  Response Time: {elapsed:.2f}s")
        
        working_rpcs.append((rpc_url, elapsed))
        
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = str(e)[:80]
        print(f"✗ Error: {error_msg}")
        print(f"  Time: {elapsed:.2f}s")
        failed_rpcs.append((rpc_url, error_msg))

# Summary
print("\n" + "=" * 80)
print("\nSUMMARY:")
print("=" * 80)

if working_rpcs:
    print(f"\n✓ Working RPCs ({len(working_rpcs)}):")
    # Sort by response time
    working_rpcs.sort(key=lambda x: x[1])
    for rpc_url, elapsed in working_rpcs:
        print(f"  • {rpc_url} ({elapsed:.2f}s)")
else:
    print("\n✗ No working RPCs found!")

if failed_rpcs:
    print(f"\n✗ Failed RPCs ({len(failed_rpcs)}):")
    for rpc_url, error in failed_rpcs:
        print(f"  • {rpc_url}")
        print(f"    Error: {error[:60]}")

print("\n" + "=" * 80)

if not working_rpcs:
    print("\n⚠️  NETWORK ISSUE DETECTED")
    print("\nPossible causes:")
    print("  1. Firewall blocking outbound HTTPS connections")
    print("  2. DNS resolution issues")
    print("  3. VPS provider blocking cryptocurrency-related domains")
    print("  4. Network connectivity problems")
    print("\nTroubleshooting:")
    print("  • Try: curl -I https://polygon-rpc.com")
    print("  • Try: ping 8.8.8.8")
    print("  • Check VPS firewall: sudo iptables -L")
    print("  • Check if requests work: pip install requests && python -c 'import requests; print(requests.get(\"https://polygon-rpc.com\").status_code)'")
    sys.exit(1)
else:
    print(f"\n✅ Network OK - {len(working_rpcs)}/{len(RPC_URLS)} RPCs working")
    print(f"\nRecommended RPC: {working_rpcs[0][0]} (fastest)")
