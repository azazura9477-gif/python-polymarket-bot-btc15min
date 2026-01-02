"""
Set allowances and deposit USDC to Polymarket for trading.

This script:
1. Approves USDC spending for Polymarket exchange contracts
2. Approves CTF (Conditional Token Framework) for trading
3. Optionally deposits USDC to your Polymarket balance

Usage:
    python deposit_usdc.py                    # Set allowances only
    python deposit_usdc.py --deposit 100      # Set allowances and deposit 100 USDC
    python deposit_usdc.py --check            # Check current allowances and balances
"""

import argparse
import json
import sys
from web3 import Web3
from web3.constants import MAX_INT
from web3.middleware import ExtraDataToPOAMiddleware


# Polygon contract addresses
USDC_ADDRESS = '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174'  # USDC on Polygon
CTF_ADDRESS = '0x4D97DCd97eC945f40cF65F87097ACe5EA0476045'   # Conditional Token Framework

# Polymarket exchange addresses
CTF_EXCHANGE = '0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E'
NEG_RISK_CTF_EXCHANGE = '0xC5d563A36AE78145C45a50134d48A1215220f80a'
NEG_RISK_ADAPTER = '0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296'

# Polygon RPC URLs (with fallbacks)
RPC_URLS = [
    'https://polygon-rpc.com',
    'https://polygon.llamarpc.com',
    'https://rpc-mainnet.matic.network',
    'https://rpc-mainnet.maticvigil.com',
    'https://polygon-bor-rpc.publicnode.com',
]
CHAIN_ID = 137

# Minimal ABIs
ERC20_APPROVE_ABI = '''[{
    "constant": false,
    "inputs": [
        {"name": "_spender", "type": "address"},
        {"name": "_value", "type": "uint256"}
    ],
    "name": "approve",
    "outputs": [{"name": "", "type": "bool"}],
    "payable": false,
    "stateMutability": "nonpayable",
    "type": "function"
}, {
    "constant": true,
    "inputs": [
        {"name": "_owner", "type": "address"},
        {"name": "_spender", "type": "address"}
    ],
    "name": "allowance",
    "outputs": [{"name": "", "type": "uint256"}],
    "stateMutability": "view",
    "type": "function"
}, {
    "constant": true,
    "inputs": [{"name": "_owner", "type": "address"}],
    "name": "balanceOf",
    "outputs": [{"name": "balance", "type": "uint256"}],
    "stateMutability": "view",
    "type": "function"
}]'''

ERC1155_SET_APPROVAL_ABI = '''[{
    "inputs": [
        {"internalType": "address", "name": "operator", "type": "address"},
        {"internalType": "bool", "name": "approved", "type": "bool"}
    ],
    "name": "setApprovalForAll",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
}, {
    "inputs": [
        {"internalType": "address", "name": "account", "type": "address"},
        {"internalType": "address", "name": "operator", "type": "address"}
    ],
    "name": "isApprovedForAll",
    "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
    "stateMutability": "view",
    "type": "function"
}]'''


def load_credentials():
    """Load private key and wallet address from config.json"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        private_key = config['api_credentials']['private_key']
        wallet_address = config['api_credentials']['wallet_address']
        
        # Remove 0x prefix if present for consistency
        if private_key.startswith('0x'):
            private_key = private_key[2:]
            
        return private_key, wallet_address
    except Exception as e:
        print(f"Error loading credentials from config.json: {e}")
        sys.exit(1)


def check_balances(web3, wallet_address):
    """Check MATIC and USDC balances"""
    # MATIC balance
    matic_balance = web3.eth.get_balance(wallet_address)
    matic_balance_eth = web3.from_wei(matic_balance, 'ether')
    
    # USDC balance
    usdc_contract = web3.eth.contract(
        address=Web3.to_checksum_address(USDC_ADDRESS),
        abi=ERC20_APPROVE_ABI
    )
    usdc_balance_raw = usdc_contract.functions.balanceOf(
        Web3.to_checksum_address(wallet_address)
    ).call()
    usdc_balance = usdc_balance_raw / 1e6  # USDC has 6 decimals
    
    print(f"\n{'='*60}")
    print(f"Wallet: {wallet_address}")
    print(f"MATIC Balance: {matic_balance_eth:.6f} MATIC")
    print(f"USDC Balance: {usdc_balance:.6f} USDC")
    print(f"{'='*60}\n")
    
    return matic_balance, usdc_balance


def check_allowances(web3, wallet_address):
    """Check current allowances for USDC and CTF"""
    usdc_contract = web3.eth.contract(
        address=Web3.to_checksum_address(USDC_ADDRESS),
        abi=ERC20_APPROVE_ABI
    )
    ctf_contract = web3.eth.contract(
        address=Web3.to_checksum_address(CTF_ADDRESS),
        abi=ERC1155_SET_APPROVAL_ABI
    )
    
    wallet_checksum = Web3.to_checksum_address(wallet_address)
    
    # Check USDC allowances
    print("Current Allowances:")
    print("-" * 60)
    
    ctf_exchange_allowance = usdc_contract.functions.allowance(
        wallet_checksum,
        Web3.to_checksum_address(CTF_EXCHANGE)
    ).call()
    print(f"USDC -> CTF Exchange: {ctf_exchange_allowance / 1e6:.2f} USDC")
    
    neg_risk_exchange_allowance = usdc_contract.functions.allowance(
        wallet_checksum,
        Web3.to_checksum_address(NEG_RISK_CTF_EXCHANGE)
    ).call()
    print(f"USDC -> Neg Risk CTF Exchange: {neg_risk_exchange_allowance / 1e6:.2f} USDC")
    
    neg_risk_adapter_allowance = usdc_contract.functions.allowance(
        wallet_checksum,
        Web3.to_checksum_address(NEG_RISK_ADAPTER)
    ).call()
    print(f"USDC -> Neg Risk Adapter: {neg_risk_adapter_allowance / 1e6:.2f} USDC")
    
    # Check CTF approvals
    ctf_exchange_approved = ctf_contract.functions.isApprovedForAll(
        wallet_checksum,
        Web3.to_checksum_address(CTF_EXCHANGE)
    ).call()
    print(f"CTF -> CTF Exchange: {'✓ Approved' if ctf_exchange_approved else '✗ Not approved'}")
    
    neg_risk_exchange_approved = ctf_contract.functions.isApprovedForAll(
        wallet_checksum,
        Web3.to_checksum_address(NEG_RISK_CTF_EXCHANGE)
    ).call()
    print(f"CTF -> Neg Risk CTF Exchange: {'✓ Approved' if neg_risk_exchange_approved else '✗ Not approved'}")
    
    neg_risk_adapter_approved = ctf_contract.functions.isApprovedForAll(
        wallet_checksum,
        Web3.to_checksum_address(NEG_RISK_ADAPTER)
    ).call()
    print(f"CTF -> Neg Risk Adapter: {'✓ Approved' if neg_risk_adapter_approved else '✗ Not approved'}")
    print("-" * 60)


def set_allowances(web3, private_key, wallet_address):
    """Set unlimited allowances for USDC and CTF contracts"""
    print("\n🔧 Setting allowances for Polymarket trading...")
    
    # Check MATIC balance
    matic_balance = web3.eth.get_balance(wallet_address)
    if matic_balance == 0:
        raise Exception('No MATIC in your wallet. You need MATIC for gas fees.')
    
    print(f"MATIC balance: {web3.from_wei(matic_balance, 'ether'):.6f} MATIC")
    
    # Initialize contracts
    usdc_contract = web3.eth.contract(
        address=Web3.to_checksum_address(USDC_ADDRESS),
        abi=ERC20_APPROVE_ABI
    )
    ctf_contract = web3.eth.contract(
        address=Web3.to_checksum_address(CTF_ADDRESS),
        abi=ERC1155_SET_APPROVAL_ABI
    )
    
    wallet_checksum = Web3.to_checksum_address(wallet_address)
    nonce = web3.eth.get_transaction_count(wallet_checksum)
    
    # Approve USDC for CTF Exchange
    print("\n1/6 Approving USDC for CTF Exchange...")
    tx = usdc_contract.functions.approve(
        Web3.to_checksum_address(CTF_EXCHANGE),
        int(MAX_INT, 0)
    ).build_transaction({
        'chainId': CHAIN_ID,
        'from': wallet_checksum,
        'nonce': nonce,
        'gas': 100000,
        'gasPrice': web3.eth.gas_price
    })
    signed_tx = web3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)
    print(f"✓ Transaction confirmed: {receipt['transactionHash'].hex()}")
    
    # Approve CTF for CTF Exchange
    nonce += 1
    print("\n2/6 Approving CTF for CTF Exchange...")
    tx = ctf_contract.functions.setApprovalForAll(
        Web3.to_checksum_address(CTF_EXCHANGE),
        True
    ).build_transaction({
        'chainId': CHAIN_ID,
        'from': wallet_checksum,
        'nonce': nonce,
        'gas': 100000,
        'gasPrice': web3.eth.gas_price
    })
    signed_tx = web3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)
    print(f"✓ Transaction confirmed: {receipt['transactionHash'].hex()}")
    
    # Approve USDC for Neg Risk CTF Exchange
    nonce += 1
    print("\n3/6 Approving USDC for Neg Risk CTF Exchange...")
    tx = usdc_contract.functions.approve(
        Web3.to_checksum_address(NEG_RISK_CTF_EXCHANGE),
        int(MAX_INT, 0)
    ).build_transaction({
        'chainId': CHAIN_ID,
        'from': wallet_checksum,
        'nonce': nonce,
        'gas': 100000,
        'gasPrice': web3.eth.gas_price
    })
    signed_tx = web3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)
    print(f"✓ Transaction confirmed: {receipt['transactionHash'].hex()}")
    
    # Approve CTF for Neg Risk CTF Exchange
    nonce += 1
    print("\n4/6 Approving CTF for Neg Risk CTF Exchange...")
    tx = ctf_contract.functions.setApprovalForAll(
        Web3.to_checksum_address(NEG_RISK_CTF_EXCHANGE),
        True
    ).build_transaction({
        'chainId': CHAIN_ID,
        'from': wallet_checksum,
        'nonce': nonce,
        'gas': 100000,
        'gasPrice': web3.eth.gas_price
    })
    signed_tx = web3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)
    print(f"✓ Transaction confirmed: {receipt['transactionHash'].hex()}")
    
    # Approve USDC for Neg Risk Adapter
    nonce += 1
    print("\n5/6 Approving USDC for Neg Risk Adapter...")
    tx = usdc_contract.functions.approve(
        Web3.to_checksum_address(NEG_RISK_ADAPTER),
        int(MAX_INT, 0)
    ).build_transaction({
        'chainId': CHAIN_ID,
        'from': wallet_checksum,
        'nonce': nonce,
        'gas': 100000,
        'gasPrice': web3.eth.gas_price
    })
    signed_tx = web3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)
    print(f"✓ Transaction confirmed: {receipt['transactionHash'].hex()}")
    
    # Approve CTF for Neg Risk Adapter
    nonce += 1
    print("\n6/6 Approving CTF for Neg Risk Adapter...")
    tx = ctf_contract.functions.setApprovalForAll(
        Web3.to_checksum_address(NEG_RISK_ADAPTER),
        True
    ).build_transaction({
        'chainId': CHAIN_ID,
        'from': wallet_checksum,
        'nonce': nonce,
        'gas': 100000,
        'gasPrice': web3.eth.gas_price
    })
    signed_tx = web3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)
    print(f"✓ Transaction confirmed: {receipt['transactionHash'].hex()}")
    
    print("\n✅ All allowances set successfully!")


def connect_to_polygon():
    """Try multiple RPC endpoints to connect to Polygon"""
    for i, rpc_url in enumerate(RPC_URLS, 1):
        try:
            print(f"Attempting connection {i}/{len(RPC_URLS)}: {rpc_url}...")
            web3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))
            web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
            
            # Test connection with a simple call
            if web3.is_connected():
                chain_id = web3.eth.chain_id
                if chain_id == CHAIN_ID:
                    print(f"✓ Connected to Polygon (chain_id: {chain_id})")
                    return web3, rpc_url
                else:
                    print(f"✗ Wrong chain (expected {CHAIN_ID}, got {chain_id})")
            else:
                print(f"✗ Connection failed")
        except Exception as e:
            print(f"✗ Error: {str(e)[:60]}")
            continue
    
    raise Exception("Failed to connect to Polygon with any RPC endpoint. Check your network connection.")


def main():
    parser = argparse.ArgumentParser(
        description='Set allowances and deposit USDC to Polymarket'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check current allowances and balances only (no transactions)'
    )
    parser.add_argument(
        '--deposit',
        type=float,
        help='Amount of USDC to deposit (after setting allowances)'
    )
    args = parser.parse_args()
    
    # Load credentials
    private_key, wallet_address = load_credentials()
    
    # Connect to Polygon with fallback RPCs
    print("Connecting to Polygon...")
    try:
        web3, rpc_url = connect_to_polygon()
    except Exception as e:
        print(f"\n❌ {e}")
        sys.exit(1)
    
    # Check balances
    matic_balance, usdc_balance = check_balances(web3, wallet_address)
    
    # Check allowances
    if args.check:
        check_allowances(web3, wallet_address)
        return
    
    # Set allowances
    try:
        set_allowances(web3, private_key, wallet_address)
    except Exception as e:
        print(f"\n❌ Error setting allowances: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Optional: Deposit info
    if args.deposit:
        print(f"\n📝 Note: Requested deposit of {args.deposit} USDC")
        print("Your USDC is now approved for trading on Polymarket.")
        print("The py-clob-client library will automatically handle deposits when placing orders.")
        print("No manual deposit transaction is needed.")
    
    print("\n✅ Setup complete! You can now trade on Polymarket.")
    print("\nNext steps:")
    print("  1. Run: python test_balance.py")
    print("  2. Run: python main.py")


if __name__ == '__main__':
    main()
