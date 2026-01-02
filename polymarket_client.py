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
    
    def find_bitcoin_15min_market(self, keywords: List[str] = None, manual_condition_id: str = None) -> Optional[Dict]:
        """
        Find the active Bitcoin Up/Down 15min market.
        
        Strategy:
        1. If manual_condition_id provided, fetch directly
        2. Generate likely slugs based on 15min timestamp intervals
        3. Scan only the first 100 markets (most recent) for matching slug
        
        Args:
            keywords: List of keywords (not used, kept for compatibility)
            manual_condition_id: Optional condition ID to fetch directly
        
        Returns:
            Market data dictionary or None if not found
        """
        try:
            # If manual condition_id is provided, try to fetch it directly
            if manual_condition_id:
                logger.info(f"Fetching market by condition_id: {manual_condition_id}")
                try:
                    market = self.client.get_market(manual_condition_id)
                    if market:
                        logger.info(f"✓ Found market: {market.get('question')}")
                        return market
                    else:
                        logger.warning(f"Market {manual_condition_id} not found or inactive")
                except Exception as e:
                    logger.error(f"Error fetching market {manual_condition_id}: {e}")
            
            # Generate likely slugs based on current time
            import time
            from datetime import datetime
            
            now = int(time.time())
            
            # Generate timestamps for 15min windows (check a range around current time)
            # Each window is 900 seconds (15 minutes)
            candidate_slugs = []
            for i in range(-2, 10):  # Check 2 past and 9 future windows (~ 2.5 hours)
                ts = now + (i * 900)
                # Round to 900-second boundary
                ts_rounded = (ts // 900) * 900
                slug = f"btc-updown-15m-{ts_rounded}"
                dt = datetime.fromtimestamp(ts_rounded)
                candidate_slugs.append((slug, ts_rounded, dt))
            
            logger.info(f"Generated {len(candidate_slugs)} candidate slugs for timestamps")
            logger.debug(f"Time range: {candidate_slugs[0][2]} to {candidate_slugs[-1][2]}")
            
            # Scan only the FIRST 100 markets (most recent) from CLOB API
            logger.info("Scanning first 100 markets from CLOB API...")
            
            try:
                response = self.client.get_markets(next_cursor="")
                
                markets = []
                if isinstance(response, dict):
                    markets = response.get('data', [])[:100]  # Only first 100
                elif isinstance(response, list):
                    markets = response[:100]
                
                logger.info(f"Retrieved {len(markets)} recent markets")
                
                # Match against our candidate slugs
                candidate_slug_set = set(slug for slug, _, _ in candidate_slugs)
                
                for market in markets:
                    if not isinstance(market, dict):
                        continue
                    
                    market_slug = market.get('slug', '')
                    
                    # Check if this market matches one of our predicted slugs
                    if market_slug in candidate_slug_set:
                        # Verify it's active and has UP/DOWN tokens
                        active = market.get('active', False)
                        closed = market.get('closed', True)
                        
                        if active and not closed:
                            tokens = market.get('tokens', [])
                            if len(tokens) == 2:
                                token_names = [t.get('outcome', '').lower() for t in tokens]
                                if 'up' in token_names and 'down' in token_names:
                                    logger.info(f"✓ Found active market: {market.get('question')}")
                                    logger.info(f"  Slug: {market_slug}")
                                    logger.info(f"  Condition ID: {market.get('condition_id')}")
                                    logger.info(f"  End date: {market.get('end_date_iso')}")
                                    return market
                
                logger.warning("No matching BTC 15min market found in recent markets")
                
            except Exception as e:
                logger.error(f"Error scanning CLOB markets: {e}")
            
            # Fallback: try a broader search (up to 500 markets)
            logger.info("Trying broader search (500 markets)...")
            try:
                response = self.client.get_markets(next_cursor="")
                markets = []
                if isinstance(response, dict):
                    markets = response.get('data', [])[:500]
                elif isinstance(response, list):
                    markets = response[:500]
                
                for market in markets:
                    if not isinstance(market, dict):
                        continue
                    
                    slug = market.get('slug', '').lower()
                    
                    # Look for btc-updown-15m pattern
                    if slug.startswith('btc-updown-15m-'):
                        active = market.get('active', False)
                        closed = market.get('closed', True)
                        
                        if active and not closed:
                            tokens = market.get('tokens', [])
                            if len(tokens) == 2:
                                token_names = [t.get('outcome', '').lower() for t in tokens]
                                if 'up' in token_names and 'down' in token_names:
                                    logger.info(f"✓ Found via broader search: {market.get('question')}")
                                    logger.info(f"  Slug: {slug}")
                                    logger.info(f"  Condition ID: {market.get('condition_id')}")
                                    return market
                
            except Exception as e:
                logger.error(f"Error in broader search: {e}")
            
            logger.warning("No active Bitcoin 15min market found")
            logger.info("💡 TIP: Provide manual_condition_id in config.json if you know the market")
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
