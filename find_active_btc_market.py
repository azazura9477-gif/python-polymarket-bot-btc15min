#!/usr/bin/env python3
"""
Trouve le marché BTC 15min actif en scrappant la page web Polymarket.
"""

import re
import json
import requests
from bs4 import BeautifulSoup
from py_clob_client.client import ClobClient
from datetime import datetime


def scrape_active_btc_market_from_web():
    """
    Scrappe la page Polymarket pour trouver les marchés BTC 15min actifs.
    """
    
    print("\n" + "="*80)
    print("RECHERCHE DE MARCHÉS BTC 15MIN ACTIFS VIA WEB SCRAPING")
    print("="*80 + "\n")
    
    # URLs à essayer
    urls_to_check = [
        "https://polymarket.com/markets",
        "https://polymarket.com/event/btc-updown-15m",
        "https://polymarket.com/?tag=BTC",
    ]
    
    for url in urls_to_check:
        print(f"🔍 Scraping: {url}")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"  ❌ Status: {response.status_code}")
                continue
            
            html = response.text
            
            # Chercher les condition_ids dans le HTML (pattern 0x...)
            condition_id_pattern = r'0x[a-fA-F0-9]{64}'
            condition_ids = re.findall(condition_id_pattern, html)
            
            if condition_ids:
                print(f"  ✓ Trouvé {len(set(condition_ids))} condition_ids uniques")
                
                # Chercher aussi les slugs btc-updown-15m
                slug_pattern = r'btc-updown-15m-\d+'
                slugs = re.findall(slug_pattern, html)
                
                if slugs:
                    print(f"  ✓ Trouvé {len(set(slugs))} slugs BTC 15min:")
                    for slug in set(slugs):
                        print(f"    - {slug}")
                
                return list(set(condition_ids)), list(set(slugs))
            else:
                print(f"  ❌ Aucun condition_id trouvé")
                
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
            continue
    
    return [], []


def check_market_status(condition_id: str, client: ClobClient) -> dict:
    """Vérifie le statut d'un marché via son condition_id."""
    
    try:
        market = client.get_market(condition_id)
        
        if not market:
            return None
        
        question = market.get('question', '')
        active = market.get('active', False)
        closed = market.get('closed', True)
        
        # Vérifier si c'est un marché BTC 15min
        if '15' not in question.lower() or 'bitcoin' not in question.lower():
            return None
        
        tokens = market.get('tokens', [])
        token_map = {}
        
        for token in tokens:
            outcome = token.get('outcome', '').upper()
            token_id = token.get('token_id', '')
            if outcome in ['UP', 'DOWN']:
                token_map[outcome] = token_id
        
        if active and not closed and len(token_map) == 2:
            return {
                'condition_id': condition_id,
                'question': question,
                'active': active,
                'closed': closed,
                'tokens': token_map,
                'end_date': market.get('end_date_iso')
            }
        
        return None
        
    except Exception as e:
        return None


def find_active_btc_15min_market():
    """Trouve un marché BTC 15min actif en combinant web scraping et API."""
    
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
    
    # Étape 1: Scraper la page web
    condition_ids, slugs = scrape_active_btc_market_from_web()
    
    if not condition_ids:
        print("\n❌ Aucun marché trouvé via web scraping")
        print("\n💡 Les marchés BTC 15min ne sont peut-être pas actifs en ce moment.")
        print("   Ils sont généralement créés pendant les heures de trading US (9h-17h ET)")
        return None
    
    # Étape 2: Vérifier chaque condition_id
    print("\n" + "="*80)
    print("VÉRIFICATION DES MARCHÉS TROUVÉS")
    print("="*80 + "\n")
    
    active_markets = []
    
    for i, cond_id in enumerate(condition_ids[:20], 1):  # Limiter à 20 pour ne pas spammer
        print(f"{i}. Vérification: {cond_id[:20]}...")
        
        market_info = check_market_status(cond_id, client)
        
        if market_info:
            print(f"   ✅ ACTIF: {market_info['question']}")
            active_markets.append(market_info)
        else:
            print(f"   ⏸️  Inactif ou non pertinent")
    
    # Étape 3: Retourner le meilleur marché
    if active_markets:
        print("\n" + "="*80)
        print(f"✅ TROUVÉ {len(active_markets)} MARCHÉ(S) ACTIF(S)")
        print("="*80 + "\n")
        
        # Prendre le premier marché actif
        best_market = active_markets[0]
        
        print(f"🎯 Marché sélectionné:")
        print(f"   Question: {best_market['question']}")
        print(f"   Condition ID: {best_market['condition_id']}")
        print(f"   Fin: {best_market['end_date']}")
        print(f"   UP: {best_market['tokens']['UP']}")
        print(f"   DOWN: {best_market['tokens']['DOWN']}")
        
        print(f"\n📋 JSON:")
        print(json.dumps(best_market, indent=2))
        
        return best_market
    else:
        print("\n❌ Aucun marché BTC 15min actif trouvé")
        print("\n💡 RAISON PROBABLE:")
        print("   • Les marchés BTC 15min sont créés uniquement pendant certaines heures")
        print("   • Heure actuelle: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print("   • Marchés généralement actifs: 9h-17h ET (14h-22h UTC)")
        return None


if __name__ == "__main__":
    result = find_active_btc_15min_market()
    
    if result:
        print("\n✅ Utilisez ce condition_id dans config.json:")
        print(f'   "manual_condition_id": "{result["condition_id"]}"')
        exit(0)
    else:
        exit(1)
