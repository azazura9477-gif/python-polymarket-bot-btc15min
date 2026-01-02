#!/usr/bin/env python3
"""
Script de diagnostic pour voir TOUS les marchés BTC disponibles.
"""

import json
from py_clob_client.client import ClobClient
from datetime import datetime

def debug_all_btc_markets():
    """Affiche tous les marchés BTC trouvés dans les 500 premiers résultats."""
    
    # Charger la config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    private_key = config['api_credentials']['private_key']
    
    # Créer le client
    client = ClobClient(
        host="https://clob.polymarket.com",
        key=private_key,
        chain_id=137
    )
    
    print("\n" + "="*80)
    print("DIAGNOSTIC: Tous les marchés BTC dans les 500 premiers résultats")
    print("="*80 + "\n")
    
    # Récupérer les marchés
    response = client.get_markets(next_cursor="")
    
    markets = []
    if isinstance(response, dict):
        markets = response.get('data', [])[:500]
    elif isinstance(response, list):
        markets = response[:500]
    
    print(f"Total markets retrieved: {len(markets)}\n")
    
    # Filtrer les marchés BTC
    btc_markets = []
    for market in markets:
        if not isinstance(market, dict):
            continue
        
        slug = market.get('slug', '').lower()
        question = market.get('question', '').lower()
        
        # Chercher BTC dans slug ou question
        if 'btc' in slug or 'bitcoin' in slug or 'btc' in question or 'bitcoin' in question:
            btc_markets.append(market)
    
    print(f"Found {len(btc_markets)} BTC-related markets\n")
    print("="*80)
    
    # Afficher tous les marchés BTC
    for i, market in enumerate(btc_markets[:50], 1):  # Limiter à 50 pour lisibilité
        slug = market.get('slug', '')
        question = market.get('question', '')
        active = market.get('active', False)
        closed = market.get('closed', True)
        condition_id = market.get('condition_id', '')
        
        # Déterminer le statut
        if active and not closed:
            status = "🟢 ACTIVE"
        elif not active and not closed:
            status = "🟡 INACTIVE"
        elif closed:
            status = "🔴 CLOSED"
        else:
            status = "⚪ UNKNOWN"
        
        print(f"\n{i}. {status}")
        print(f"   Slug: {slug}")
        print(f"   Question: {question[:80]}...")
        print(f"   Condition ID: {condition_id}")
        print(f"   Active: {active} | Closed: {closed}")
        
        # Si c'est un marché 15min, afficher les détails
        if '15m' in slug or '15min' in slug.lower():
            tokens = market.get('tokens', [])
            print(f"   Tokens: {len(tokens)}")
            for token in tokens:
                print(f"     - {token.get('outcome')}: {token.get('token_id')}")
            
            end_date = market.get('end_date_iso', '')
            if end_date:
                print(f"   End date: {end_date}")
    
    print("\n" + "="*80)
    
    # Chercher spécifiquement les patterns btc-updown-15m
    print("\nMarchés avec pattern 'btc-updown-15m-*':")
    print("="*80)
    
    updown_markets = [m for m in btc_markets if m.get('slug', '').startswith('btc-updown-15m-')]
    
    if updown_markets:
        for market in updown_markets:
            slug = market.get('slug', '')
            active = market.get('active', False)
            closed = market.get('closed', True)
            
            status = "ACTIVE" if (active and not closed) else "CLOSED"
            print(f"  - {slug}: {status}")
    else:
        print("  ❌ Aucun marché 'btc-updown-15m-*' trouvé")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    debug_all_btc_markets()
