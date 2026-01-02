from create_wallet import create_wallet


def test_create_wallet_formats():
    priv, addr = create_wallet()
    # private key: 0x + 64 hex chars
    assert isinstance(priv, str) and priv.startswith('0x') and len(priv) >= 66
    # address: 0x + 40 hex chars
    assert isinstance(addr, str) and addr.startswith('0x') and len(addr) == 42
