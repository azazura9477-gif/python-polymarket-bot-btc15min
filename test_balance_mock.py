#!/usr/bin/env python3
"""
Petit script de test local pour valider la normalisation du champ "balance"
sans nécessiter de clé privée ni d'accès réseau.
"""
from typing import Any


def normalize_balance(usdc_balance_raw: Any) -> float:
    if usdc_balance_raw is None:
        return 0.0
    try:
        return float(usdc_balance_raw)
    except (ValueError, TypeError):
        try:
            int_val = int(usdc_balance_raw)
            return int_val / 1e6
        except Exception:
            return 0.0


if __name__ == "__main__":
    samples = [
        "0",
        "0.0",
        "1000000",   # 1 USDC in 6-decimal base units
        1000000,      # integer base units
        "1500000",   # 1.5 USDC
        "1.5",
        None,
        "not-a-number",
    ]

    print("Testing normalize_balance on sample inputs:\n")
    for s in samples:
        print(f"raw={s!r:16} -> normalized={normalize_balance(s)}")

    print("\nMock response example (same shape que l'API):")
    mock_resp = {"balance": "1000000", "allowances": {"0xabc...": "0"}}
    print(mock_resp)
    print("Normalized balance:", normalize_balance(mock_resp.get('balance')))
