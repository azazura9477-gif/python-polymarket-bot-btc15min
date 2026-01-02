#!/usr/bin/env python3
"""
Petit script de test local pour valider la normalisation du champ "balance"
sans nécessiter de clé privée ni d'accès réseau.
"""
from typing import Any


def normalize_balance(usdc_balance_raw: Any) -> float:
    if usdc_balance_raw is None:
        return 0.0

    # Integers: likely base units (e.g. 1000000 == 1 USDC)
    if isinstance(usdc_balance_raw, int):
        return usdc_balance_raw / 1e6 if usdc_balance_raw >= 1_000_000 else float(usdc_balance_raw)

    # Floats: already human-readable USDC
    if isinstance(usdc_balance_raw, float):
        return usdc_balance_raw

    # Strings: handle decimals and integer-like base-units
    if isinstance(usdc_balance_raw, str):
        s = usdc_balance_raw.strip()
        if not s:
            return 0.0
        # If contains a dot, parse as float
        if '.' in s:
            try:
                return float(s)
            except Exception:
                return 0.0
        # Digit-only string: interpret as base units if large
        if s.lstrip('-').isdigit():
            try:
                int_val = int(s)
                return int_val / 1e6 if abs(int_val) >= 1_000_000 else float(int_val)
            except Exception:
                return 0.0
        # Fallback
        try:
            return float(s)
        except Exception:
            return 0.0

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
