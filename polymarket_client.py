"""
Polymarket API client wrapper for market detection and trading operations.
"""
import logging
from typing import Optional, Dict, List, Tuple
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType
from py_clob_client.constants import POLYGON


logger = logging.getLogger("PolymarketBot")


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
        except Exception as e:
            logger.error(f"Failed to initialize Polymarket client: {e}")
            raise
    
    def find_bitcoin_15min_market(self, keywords: List[str]) -> Optional[Dict]:
        """
        Find the active Bitcoin Up/Down 15min market.
        
        Args:
            keywords: List of keywords to search for in market title
        
        Returns:
            Market data dictionary or None if not found
        """
        try:
            next_cursor = ""
            scanned_count = 0
            
            while True:
                # Get active markets with pagination
                response = self.client.get_markets(next_cursor=next_cursor)
                
                markets = []
                if isinstance(response, dict):
                    markets = response.get('data', [])
                    next_cursor = response.get('next_cursor', "")
                elif isinstance(response, list):
                    markets = response
                    next_cursor = ""
                else:
                    logger.warning(f"Unexpected response type: {type(response)}")
                    break
                
                if not markets:
                    break
                    
                scanned_count += len(markets)
                logger.debug(f"Scanning page... (Total scanned: {scanned_count})")
                
                # Search for Bitcoin 15min market
                for market in markets:
                    # Ensure market is a dictionary
                    if not isinstance(market, dict):
                        continue
                        
                    title = market.get('question', '').lower()
                    
                    # Check if all required keywords are in the title
                    if all(keyword.lower() in title for keyword in ['bitcoin', '15']):
                        # Check if it's an Up/Down market
                        tokens = market.get('tokens', [])
                        if len(tokens) == 2:
                            token_names = [t.get('outcome', '').lower() for t in tokens]
                            if 'up' in token_names and 'down' in token_names:
                                logger.info(f"Found Bitcoin 15min market: {market.get('question')} (ID: {market.get('condition_id')})")
                                return market
                
                # Stop if no next page
                if not next_cursor or next_cursor == "0":
                    break
            
            logger.warning(f"No active Bitcoin 15min Up/Down market found after scanning {scanned_count} markets")
            return None
            
        except Exception as e:
            logger.error(f"Error searching for market: {e}")
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
            balance = self.client.get_balance()
            usdc_balance = float(balance.get('usdc', 0))
            logger.info(f"Current USDC balance: {usdc_balance}")
            return usdc_balance
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return None
