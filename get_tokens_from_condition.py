#!/usr/bin/env python3
"""
Récupère les Token IDs (UP/DOWN ou YES/NO) à partir d'un Condition ID.
Utilise deux méthodes : CLOB API et Gamma API.
"""

import json
import sys
import requests
from py_clob_client.client import ClobClient


def get_tokens_via_clob_api(condition_id: str, private_key: str) -> dict:
    """
    Méthode 1: Récupération via CLOB API (la plus directe).
    
    Args:
        condition_id: Le Condition ID du marché (0x...)
        private_key: Clé privée pour l'authentification
    
    Returns:
        Dict avec 'tokens', 'question', 'slug', etc.
    """
    print("\n" + "="*80)
    print("MÉTHODE 1: CLOB API (py-clob-client)")
    print("="*80)
    
    try:
        client = ClobClient(
            host="https://clob.polymarket.com",
            key=private_key,
            chain_id=137
        )
        
        print(f"Recherche du marché: {condition_id}")
        
        # Récupérer le marché directement par condition_id
        market = client.get_market(condition_id)
        
        if not market:
            print("❌ Marché non trouvé")
            return None
        
        print(f"✅ Marché trouvé!")
        print(f"Question: {market.get('question')}")
        print(f"Slug: {market.get('slug')}")
        print(f"Active: {market.get('active')}")
        print(f"Closed: {market.get('closed')}")
        
        tokens = market.get('tokens', [])
        print(f"\nTokens ({len(tokens)}):")
        
        result = {
            'condition_id': condition_id,
            'question': market.get('question'),
            'slug': market.get('slug'),
            'active': market.get('active'),
            'closed': market.get('closed'),
            'tokens': {}
        }
        
        for token in tokens:
            outcome = token.get('outcome', '').upper()
            token_id = token.get('token_id', '')
            print(f"  - {outcome}: {token_id}")
            result['tokens'][outcome] = token_id
        
        return result
        
    except Exception as e:
        print(f"❌ Erreur CLOB API: {e}")
        return None


def get_tokens_via_gamma_api(condition_id: str) -> dict:
    """
    Méthode 2: Récupération via Gamma API (publique, pas besoin de clé).
    
    Args:
        condition_id: Le Condition ID du marché (0x...)
    
    Returns:
        Dict avec 'tokens', 'question', 'slug', etc.
    """
    print("\n" + "="*80)
    print("MÉTHODE 2: GAMMA API (publique)")
    print("="*80)
    
    try:
        # Essayer différentes URL possibles
        urls_to_try = [
            f"https://gamma-api.polymarket.com/markets/{condition_id}",
            f"https://gamma-api.polymarket.com/markets?id={condition_id}",
            f"https://gamma-api.polymarket.com/markets?condition_id={condition_id}",
        ]
        
        for url in urls_to_try:
            print(f"\nEssai: {url}")
            
            try:
                response = requests.get(url, timeout=10)
                
                if response.status_code != 200:
                    print(f"  Status: {response.status_code}")
                    continue
                
                data = response.json()
                
                # Gérer liste ou objet unique
                if isinstance(data, list):
                    if not data:
                        print("  Liste vide")
                        continue
                    market_data = data[0]
                else:
                    market_data = data
                
                # Vérifier que c'est bien le bon marché
                if market_data.get('condition_id') != condition_id and market_data.get('id') != condition_id:
                    print("  Mauvais marché retourné")
                    continue
                
                print(f"✅ Marché trouvé!")
                print(f"Question: {market_data.get('question')}")
                print(f"Slug: {market_data.get('slug')}")
                print(f"Active: {market_data.get('active')}")
                print(f"Closed: {market_data.get('closed')}")
                
                # Les Token IDs peuvent être dans 'clobTokenIds' ou 'tokens'
                token_ids = market_data.get('clobTokenIds', [])
                tokens_info = market_data.get('tokens', [])
                
                result = {
                    'condition_id': condition_id,
                    'question': market_data.get('question'),
                    'slug': market_data.get('slug'),
                    'active': market_data.get('active'),
                    'closed': market_data.get('closed'),
                    'tokens': {}
                }
                
                print(f"\nTokens:")
                
                # Méthode 1: clobTokenIds (array simple)
                if token_ids and len(token_ids) >= 2:
                    # Convention: [YES/UP, NO/DOWN] ou [token0, token1]
                    outcomes = market_data.get('outcomes', ['YES', 'NO'])
                    for i, token_id in enumerate(token_ids):
                        outcome = outcomes[i] if i < len(outcomes) else f"Token{i}"
                        print(f"  - {outcome}: {token_id}")
                        result['tokens'][outcome.upper()] = token_id
                
                # Méthode 2: tokens (objets détaillés)
                elif tokens_info:
                    for token in tokens_info:
                        outcome = token.get('outcome', '').upper()
                        token_id = token.get('token_id', '')
                        print(f"  - {outcome}: {token_id}")
                        result['tokens'][outcome] = token_id
                
                if result['tokens']:
                    return result
                else:
                    print("  ❌ Aucun token ID trouvé")
                    continue
                    
            except Exception as e:
                print(f"  Erreur: {e}")
                continue
        
        print("\n❌ Aucune URL n'a fonctionné")
        return None
        
    except Exception as e:
        print(f"❌ Erreur Gamma API: {e}")
        return None


def main():
    """Récupère les tokens via les deux méthodes."""
    
    if len(sys.argv) < 2:
        print("Usage: python get_tokens_from_condition.py <condition_id>")
        print("Exemple: python get_tokens_from_condition.py 0x0b5dc0a884f89ff3bc3a847d697fba8acc6cf86f1c9518761e325896a63d5af5")
        sys.exit(1)
    
    condition_id = sys.argv[1]
    
    print("\n" + "="*80)
    print(f"RÉCUPÉRATION DES TOKEN IDS POUR: {condition_id}")
    print("="*80)
    
    # Charger la config pour la méthode CLOB
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        private_key = config['api_credentials']['private_key']
    except Exception as e:
        print(f"⚠️  Impossible de charger config.json: {e}")
        print("La méthode CLOB API sera ignorée")
        private_key = None
    
    # Essayer les deux méthodes
    result_clob = None
    result_gamma = None
    
    if private_key:
        result_clob = get_tokens_via_clob_api(condition_id, private_key)
    
    result_gamma = get_tokens_via_gamma_api(condition_id)
    
    # Afficher le résumé final
    print("\n" + "="*80)
    print("RÉSUMÉ")
    print("="*80)
    
    final_result = result_clob or result_gamma
    
    if final_result:
        print(f"\n✅ SUCCESS!\n")
        print(f"Condition ID: {final_result['condition_id']}")
        print(f"Question: {final_result['question']}")
        print(f"Slug: {final_result['slug']}")
        print(f"Active: {final_result['active']} | Closed: {final_result['closed']}")
        print(f"\nToken IDs:")
        for outcome, token_id in final_result['tokens'].items():
            print(f"  {outcome}: {token_id}")
        
        print(f"\n📋 JSON:")
        print(json.dumps(final_result, indent=2))
        
        return 0
    else:
        print("\n❌ Échec des deux méthodes")
        return 1


if __name__ == "__main__":
    sys.exit(main())
