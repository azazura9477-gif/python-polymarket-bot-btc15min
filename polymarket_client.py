"""
Polymarket API client wrapper for market detection and trading operations.
"""
import logging
import requests
import time
import re
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
        2. Scrape Polymarket web page for current active market
        3. Extract condition_id from HTML and fetch via API
        
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
            
            # NEW STRATEGY: Scrape web page to find active market
            logger.info("🌐 Scraping Polymarket web to find active BTC 15min market...")
            
            now = int(time.time())
            
            # Generate URLs for the next 7 windows (1.75 hours)
            for i in range(0, 7):
                ts = now + (i * 900)
                ts_rounded = (ts // 900) * 900
                url = f"https://polymarket.com/event/btc-updown-15m-{ts_rounded}"
                
                try:
                    logger.info(f"  Checking: btc-updown-15m-{ts_rounded}")
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                    response = requests.get(url, headers=headers, timeout=5)
                    
                    if response.status_code == 200:
                        # Extract condition_id from HTML using regex
                        html = response.text
                        pattern = r'0x[a-fA-F0-9]{64}'
                        condition_ids = re.findall(pattern, html)
                        
                        if condition_ids:
                            # Take the first condition_id found
                            condition_id = condition_ids[0]
                            logger.info(f"  ✓ Found condition_id: {condition_id[:20]}...")
                            
                            # Fetch market via API
                            market = self.client.get_market(condition_id)
                            
                            if market:
                                active = market.get('active', False)
                                closed = market.get('closed', True)
                                
                                if active and not closed:
                                    logger.info(f"✅ Found active market!")
                                    logger.info(f"   Question: {market.get('question')}")
                                    logger.info(f"   Condition ID: {condition_id}")
                                    
                                    # Verify UP/DOWN tokens exist
                                    tokens = market.get('tokens', [])
                                    if len(tokens) == 2:
                                        token_names = [t.get('outcome', '').upper() for t in tokens]
                                        if 'UP' in token_names and 'DOWN' in token_names:
                                            return market
                                
                                logger.info(f"  Market found but not active/closed")
                        else:
                            logger.debug(f"  No condition_id found in HTML")
                    else:
                        logger.debug(f"  Status {response.status_code}")
                        
                except Exception as e:
                    logger.debug(f"  Error: {e}")
                    continue
            
            logger.warning("No active BTC 15min market found via web scraping")
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
                
                # OrderBookSummary is an object, not a dict - access attributes directly
                if hasattr(orderbook, 'asks') and orderbook.asks:
                    best_ask = float(orderbook.asks[0].price)
                    prices[outcome] = best_ask
                elif hasattr(orderbook, 'bids') and orderbook.bids:
                    best_bid = float(orderbook.bids[0].price)
                    prices[outcome] = best_bid
                else:
                    # Fallback to last price from market data
                    prices[outcome] = float(token.get('price', 0.5))
            
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
