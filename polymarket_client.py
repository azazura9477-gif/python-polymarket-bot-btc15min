"""
Polymarket API client wrapper for market detection and trading operations.
"""
import logging
import requests
from typing import Optional, Dict, List, Tuple
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType, BalanceAllowanceParams, AssetType
from py_clob_client.constants import POLYGON


logger = logging.getLogger("PolymarketBot")

# Polymarket Gamma API endpoint
GAMMA_API_URL = "https://gamma-api.polymarket.com"


class PolymarketClient:
    """Wrapper for Polymarket CLOB API interactions."""
    
    def __init__(self, private_key: str, wallet_address: str):
        """
        Initialize the Polymarket client.
        
        Args:
            private_key: Private key for signing transactions (hex format)
            wallet_address: Wallet address
        """
        self.private_key = private_key
        self.wallet_address = wallet_address
        
        # Initialize CLOB client
        # The API key is automatically derived from the private key by py-clob-client
        try:
            self.client = ClobClient(
                host="https://clob.polymarket.com",
                key=private_key,
                chain_id=POLYGON
            )
            logger.info("Polymarket client initialized successfully")
            logger.info(f"Connected with wallet: {wallet_address}")
            
            # Perform Level 1 authentication (required before Level 2)
            try:
                self.client.assert_level_1_auth()
                logger.info("Level 1 authentication successful")
            except Exception as auth_error:
                logger.warning(f"Level 1 auth warning: {auth_error}")
            
            # Create or derive API credentials for authenticated endpoints
            try:
                api_creds = self.client.create_or_derive_api_creds()
                self.client.set_api_creds(api_creds)
                logger.info("API credentials created and set successfully")
            except Exception as auth_error:
                logger.warning(f"Could not create/derive API credentials: {auth_error}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Polymarket client: {e}")
            raise
    
    def find_bitcoin_15min_market(self, keywords: List[str]) -> Optional[Dict]:
        """
        Find the active Bitcoin Up/Down 15min market by generating likely slugs.
        
        BTC 15min markets follow the pattern: btc-updown-15m-{timestamp}
        where timestamp is rounded to 15-minute intervals.
        
        Args:
            keywords: List of keywords (not used, kept for compatibility)
        
        Returns:
            Market data dictionary or None if not found
        """
        try:
            import time
            from datetime import datetime
            
            logger.info("Searching for Bitcoin 15min markets by timestamp prediction...")
            
            # Generate likely timestamps for current and next 15min windows
            now = int(time.time())
            
            # Generate timestamps for the next hour (4 x 15min windows)
            candidate_timestamps = []
            for i in range(-2, 8):  # Check 2 windows back and 7 forward
                ts = now + (i * 15 * 60)
                # Round to 15-minute boundary
                ts_rounded = (ts // (15 * 60)) * (15 * 60)
                if ts_rounded not in candidate_timestamps:
                    candidate_timestamps.append(ts_rounded)
            
            logger.info(f"Checking {len(candidate_timestamps)} potential 15min windows...")
            
            # Try each potential slug
            for ts in candidate_timestamps:
                slug = f"btc-updown-15m-{ts}"
                dt = datetime.fromtimestamp(ts)
                
                try:
                    # Try to get market from Gamma API by slug
                    url = f"{GAMMA_API_URL}/markets/{slug}"
                    response = requests.get(url, timeout=5)
                    
                    if response.status_code == 200:
                        market_data = response.json()
                        
                        # Check if market is active and not closed
                        if market_data.get('active') and not market_data.get('closed'):
                            logger.info(f"✓ Found active market: {slug} (ends {dt})")
                            
                            # Convert to CLOB format
                            outcomes = market_data.get('outcomes', [])
                            if isinstance(outcomes, str):
                                import json
                                outcomes = json.loads(outcomes)
                            
                            clob_token_ids = market_data.get('clobTokenIds', [])
                            if isinstance(clob_token_ids, str):
                                import json
                                clob_token_ids = json.loads(clob_token_ids)
                            
                            tokens = []
                            for idx, outcome in enumerate(outcomes):
                                token_id = clob_token_ids[idx] if idx < len(clob_token_ids) else None
                                tokens.append({
                                    'outcome': outcome,
                                    'token_id': token_id,
                                    'price': None
                                })
                            
                            market = {
                                'question': market_data.get('question'),
                                'condition_id': market_data.get('conditionId'),
                                'slug': slug,
                                'end_date_iso': market_data.get('endDate'),
                                'active': True,
                                'closed': False,
                                'tokens': tokens
                            }
                            
                            logger.info(f"Market: {market.get('question')}")
                            logger.info(f"Condition ID: {market.get('condition_id')}")
                            logger.info(f"Tokens: {[t['outcome'] for t in tokens]}")
                            
                            return market
                    
                except Exception as e:
                    # Skip this timestamp if error
                    continue
            
            logger.warning(f"No active Bitcoin 15min market found in checked time windows")
            logger.info(f"Checked timestamps from {datetime.fromtimestamp(candidate_timestamps[0])} to {datetime.fromtimestamp(candidate_timestamps[-1])}")
            return None
            
        except Exception as e:
            logger.error(f"Error searching for market: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_current_prices(self, market_id: str) -> Optional[Dict[str, float]]:
        """
        Get current bid/ask prices for UP and DOWN tokens.
        
        Args:
            market_id: Market identifier
        
        Returns:
            Dictionary with 'UP' and 'DOWN' prices, or None on error
        """
        try:
            # Get orderbook for the market
            market = self.client.get_market(market_id)
            tokens = market.get('tokens', [])
            
            prices = {}
            for token in tokens:
                outcome = token.get('outcome', '').upper()
                token_id = token.get('token_id')
                
                # Get best bid price (what we can sell for)
                # Get best ask price (what we can buy for)
                orderbook = self.client.get_order_book(token_id)
                
                # Use mid price or best ask for buying
                asks = orderbook.get('asks', [])
                if asks:
                    best_ask = float(asks[0]['price'])
                    prices[outcome] = best_ask
                else:
                    # Fallback to last price
                    prices[outcome] = float(token.get('price', 0))
            
            return prices
            
        except Exception as e:
            logger.error(f"Error fetching prices: {e}")
            return None
    
    def place_order(self, token_id: str, side: str, size: float, price: float) -> Optional[str]:
        """
        Place a buy or sell order.
        
        Args:
            token_id: Token identifier
            side: 'BUY' or 'SELL'
            size: Number of shares
            price: Price per share
        
        Returns:
            Order ID if successful, None otherwise
        """
        try:
            order_args = OrderArgs(
                token_id=token_id,
                price=price,
                size=size,
                side=side,
                order_type=OrderType.GTC  # Good Till Cancelled
            )
            
            order = self.client.create_order(order_args)
            order_id = order.get('orderID')
            
            logger.info(f"Order placed: {side} {size} shares at {price} - Order ID: {order_id}")
            return order_id
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    def get_token_id(self, market: Dict, outcome: str) -> Optional[str]:
        """
        Get token ID for a specific outcome (UP or DOWN).
        
        Args:
            market: Market data dictionary
            outcome: 'UP' or 'DOWN'
        
        Returns:
            Token ID or None
        """
        tokens = market.get('tokens', [])
        for token in tokens:
            if token.get('outcome', '').upper() == outcome.upper():
                return token.get('token_id')
        return None
    
    def get_balance(self) -> Optional[float]:
        """
        Get USDC balance.
        
        Returns:
            USDC balance or None on error
        """
        try:
            # Create params for COLLATERAL asset type (USDC)
            params = BalanceAllowanceParams(asset_type=AssetType.COLLATERAL)

            # Use get_balance_allowance to fetch USDC balance
            balance_allowance = self.client.get_balance_allowance(params=params)

            # The response contains balance information; be robust to multiple formats
            usdc_balance_raw = None
            if isinstance(balance_allowance, dict):
                usdc_balance_raw = balance_allowance.get('balance')

            # Normalize to float USDC amount with robust heuristics
            def _normalize(raw):
                if raw is None:
                    return 0.0
                if isinstance(raw, int):
                    return raw / 1e6 if raw >= 1_000_000 else float(raw)
                if isinstance(raw, float):
                    return raw
                if isinstance(raw, str):
                    s = raw.strip()
                    if not s:
                        return 0.0
                    if '.' in s:
                        try:
                            return float(s)
                        except Exception:
                            return 0.0
                    if s.lstrip('-').isdigit():
                        try:
                            int_val = int(s)
                            return int_val / 1e6 if abs(int_val) >= 1_000_000 else float(int_val)
                        except Exception:
                            return 0.0
                    try:
                        return float(s)
                    except Exception:
                        return 0.0
                return 0.0

            usdc_balance = _normalize(usdc_balance_raw)

            logger.info(f"Current USDC balance: {usdc_balance}")
            return usdc_balance
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return None
