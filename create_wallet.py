"""
Create a new Ethereum wallet (private key + address) and optionally save to config.json

Usage:
    python create_wallet.py            # prints keys
    python create_wallet.py --save     # saves to config.json (won't overwrite existing api_credentials)
    python create_wallet.py --save config.json --force  # overwrite existing api_credentials
"""

import argparse
import json
from pathlib import Path
from eth_account import Account


def create_wallet() -> tuple[str, str]:
    """Create a new Ethereum wallet and return (private_key_hex, address).

    The private key is returned as a 0x-prefixed hex string.
    """
    acct = Account.create()
    private_key = '0x' + acct.key.hex()
    address = acct.address
    return private_key, address


def save_to_config(private_key: str, address: str, config_path: str = 'config.json', force: bool = False) -> str:
    """Save the generated keys into the given config file under `api_credentials`.

    If the file doesn't exist it will be created. If `api_credentials` already
    exists and `force` is False, a FileExistsError is raised.
    """
    p = Path(config_path)

    if p.exists():
        with p.open('r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {}

    if 'api_credentials' in config and not force:
        raise FileExistsError(f"{config_path} already contains 'api_credentials'. Use --force to overwrite.")

    config['api_credentials'] = {
        'private_key': private_key,
        'wallet_address': address
    }

    with p.open('w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

    return str(p.resolve())


def main() -> None:
    parser = argparse.ArgumentParser(description='Create a new Ethereum wallet for the Polymarket bot')
    parser.add_argument('--save', '-s', nargs='?', const='config.json', help='Save keys to config.json (path)')
    parser.add_argument('--force', '-f', action='store_true', help='Overwrite existing api_credentials in the config file')
    args = parser.parse_args()

    private_key, address = create_wallet()

    print('Private key:', private_key)
    print('Wallet address:', address)

    if args.save:
        try:
            path = save_to_config(private_key, address, config_path=args.save, force=args.force)
            print(f"Saved keys to {path}")
        except FileExistsError as e:
            print(f"Aborted: {e}")


if __name__ == '__main__':
    main()
