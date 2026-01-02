#!/usr/bin/env python3
"""
Module pour trouver les marchés BTC 15min actifs via timestamp.
"""

import time
from datetime import datetime
from typing import Optional, Dict, Tuple
from py_clob_client.client import ClobClient
import logging

logger = logging.getLogger(__name__)


def get_current_15min_window_timestamp() -> int:
    """
    Calcule le timestamp du prochain marché BTC 15min.
    Les marchés sont créés toutes les 15 minutes (900 secondes).
    
    Returns:
        Timestamp Unix arrondi au prochain intervalle de 900 secondes
    """
    now = int(time.time())
    # Arrondir au prochain intervalle de 900 secondes
    next_window = ((now // 900) + 1) * 900
    return next_window


def get_market_by_timestamp(client: ClobClient, timestamp: int) -> Optional[Dict]:
    """
    Recherche un marché BTC 15min spécifique par son timestamp.
    
    Args:
        client: Client CLOB Polymarket
        timestamp: Timestamp Unix du marché (doit être aligné sur 900s)
    
    Returns:
        Dictionnaire du marché avec tokens, ou None si non trouvé
    """
    slug = f"btc-updown-15m-{timestamp}"
    dt = datetime.fromtimestamp(timestamp)
    
    logger.info(f"🔍 Searching for market: {slug}")
    logger.info(f"   Timestamp: {timestamp}")
    logger.info(f"   Time: {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    try:
        # Chercher dans les premiers marchés récents
        response = client.get_markets(next_cursor="")
        
        markets = []
        if isinstance(response, dict):
            markets = response.get('data', [])
        elif isinstance(response, list):
            markets = response
        
        # Chercher le slug exact
        for market in markets[:200]:  # Vérifier les 200 premiers
            if not isinstance(market, dict):
                continue
            
            market_slug = market.get('slug', '')
            if market_slug == slug:
                active = market.get('active', False)
                closed = market.get('closed', True)
                
                logger.info(f"✓ Found market!")
                logger.info(f"  Active: {active}")
                logger.info(f"  Closed: {closed}")
                logger.info(f"  Question: {market.get('question')}")
                logger.info(f"  Condition ID: {market.get('condition_id')}")
                
                if active and not closed:
                    return market
                else:
                    logger.warning("Market found but not active/already closed")
                    return None
        
        logger.warning(f"Market {slug} not found in recent markets")
        return None
        
    except Exception as e:
        logger.error(f"Error searching for market: {e}")
        return None


def get_token_ids_for_current_market(client: ClobClient) -> Optional[Dict[str, str]]:
    """
    Trouve le marché BTC 15min actuel et retourne les token IDs UP et DOWN.
    Essaie plusieurs fenêtres temporelles (actuelle et prochaines).
    
    Args:
        client: Client CLOB Polymarket initialisé
    
    Returns:
        Dict avec 'UP' et 'DOWN' token IDs, ou None si aucun marché actif trouvé
        Exemple: {'UP': '12345', 'DOWN': '67890', 'condition_id': '0x...', 'slug': '...'}
    """
    now = int(time.time())
    
    # Essayer plusieurs fenêtres : actuelle et les 6 prochaines (1h30)
    for i in range(0, 7):
        ts = now + (i * 900)
        ts_rounded = (ts // 900) * 900
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Attempt {i+1}/7: Checking window at {datetime.fromtimestamp(ts_rounded)}")
        logger.info(f"{'='*60}")
        
        market = get_market_by_timestamp(client, ts_rounded)
        
        if market:
            # Extraire les token IDs
            tokens = market.get('tokens', [])
            
            if len(tokens) != 2:
                logger.warning(f"Market has {len(tokens)} tokens instead of 2")
                continue
            
            # Identifier UP et DOWN
            token_map = {}
            for token in tokens:
                outcome = token.get('outcome', '').upper()
                token_id = token.get('token_id', '')
                
                if outcome in ['UP', 'DOWN']:
                    token_map[outcome] = token_id
            
            if 'UP' in token_map and 'DOWN' in token_map:
                result = {
                    'UP': token_map['UP'],
                    'DOWN': token_map['DOWN'],
                    'condition_id': market.get('condition_id'),
                    'slug': market.get('slug'),
                    'question': market.get('question'),
                    'end_date': market.get('end_date_iso'),
                    'timestamp': ts_rounded
                }
                
                logger.info(f"\n{'='*60}")
                logger.info(f"✅ SUCCESS! Found active BTC 15min market")
                logger.info(f"{'='*60}")
                logger.info(f"Market: {result['question']}")
                logger.info(f"Slug: {result['slug']}")
                logger.info(f"Condition ID: {result['condition_id']}")
                logger.info(f"UP Token ID: {result['UP']}")
                logger.info(f"DOWN Token ID: {result['DOWN']}")
                logger.info(f"End: {result['end_date']}")
                logger.info(f"{'='*60}\n")
                
                return result
            else:
                logger.warning(f"Could not identify UP/DOWN tokens: {[t.get('outcome') for t in tokens]}")
    
    logger.error("❌ No active BTC 15min market found in next 1.5 hours")
    return None


def find_market_by_condition_id(client: ClobClient, condition_id: str) -> Optional[Dict[str, str]]:
    """
    Trouve un marché par son condition_id et retourne les token IDs.
    
    Args:
        client: Client CLOB Polymarket
        condition_id: Condition ID du marché (0x...)
    
    Returns:
        Dict avec token IDs ou None
    """
    try:
        logger.info(f"🔍 Searching for market with condition_id: {condition_id}")
        
        market = client.get_market(condition_id)
        
        if not market:
            logger.error("Market not found")
            return None
        
        tokens = market.get('tokens', [])
        
        if len(tokens) != 2:
            logger.warning(f"Market has {len(tokens)} tokens instead of 2")
            return None
        
        token_map = {}
        for token in tokens:
            outcome = token.get('outcome', '').upper()
            token_id = token.get('token_id', '')
            if outcome in ['UP', 'DOWN']:
                token_map[outcome] = token_id
        
        if 'UP' in token_map and 'DOWN' in token_map:
            result = {
                'UP': token_map['UP'],
                'DOWN': token_map['DOWN'],
                'condition_id': condition_id,
                'slug': market.get('slug'),
                'question': market.get('question')
            }
            
            logger.info(f"✅ Market found!")
            logger.info(f"UP: {result['UP']}")
            logger.info(f"DOWN: {result['DOWN']}")
            
            return result
        
        return None
        
    except Exception as e:
        logger.error(f"Error finding market: {e}")
        return None


if __name__ == "__main__":
    # Test
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    import sys
    import json
    
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
    print("TEST: Finding current BTC 15min market by timestamp")
    print("="*80 + "\n")
    
    result = get_token_ids_for_current_market(client)
    
    if result:
        print("\n" + "="*80)
        print("RESULT:")
        print("="*80)
        print(json.dumps(result, indent=2))
        print("="*80 + "\n")
        sys.exit(0)
    else:
        print("\n❌ No market found")
        sys.exit(1)
