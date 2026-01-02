"""
Main orchestration script for the Polymarket trading bot.

This bot automatically trades on Polymarket's Bitcoin 15min Up/Down market based on:
- Entry: 5% price increase from low OR price > $0.60
- Exit: 5% price drop from position high (then flip to inverse position)
"""
import json
import time
import signal
import sys
from typing import Optional
from pathlib import Path

from logger_config import setup_logger
from polymarket_client import PolymarketClient
from trading_strategy import TradingStrategy
from position_tracker import PositionTracker


class PolymarketTradingBot:
    """Main trading bot orchestrator."""
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the trading bot.
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Setup logger
        self.logger = setup_logger(
            self.config['logging']['log_file'],
            self.config['logging']['log_level']
        )
        
        # Initialize components
        self.client = PolymarketClient(
            private_key=self.config['api_credentials']['private_key'],
            wallet_address=self.config['api_credentials']['wallet_address']
        )
        
        self.strategy = TradingStrategy(
            entry_threshold_percent=self.config['trading_parameters']['entry_threshold_percent'],
            entry_price_threshold=self.config['trading_parameters']['entry_price_threshold'],
            exit_reversal_percent=self.config['trading_parameters']['exit_reversal_percent']
        )
        
        self.position_tracker = PositionTracker()
        
        # Trading parameters
        self.position_value_usdc = self.config['trading_parameters']['position_value_usdc']
        self.check_interval = self.config['trading_parameters']['check_interval_seconds']
        
        # Market state
        self.current_market = None
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("=" * 80)
        self.logger.info("Polymarket Trading Bot Initialized")
        self.logger.info(f"Position Size: ${self.position_value_usdc} USDC")
        self.logger.info(f"Check Interval: {self.check_interval}s")
        self.logger.info("=" * 80)
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load config from {config_path}: {e}")
            sys.exit(1)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info("Shutdown signal received, stopping bot...")
        self.running = False
    
    def find_market(self) -> bool:
        """
        Find the active Bitcoin 15min Up/Down market.
        
        Returns:
            True if market found, False otherwise
        """
        self.logger.info("Searching for Bitcoin 15min Up/Down market...")
        
        manual_condition_id = self.config['market_settings'].get('manual_condition_id')
        
        market = self.client.find_bitcoin_15min_market(
            keywords=self.config['market_settings']['market_keywords'],
            manual_condition_id=manual_condition_id
        )
        
        if market:
            self.current_market = market
            self.logger.info(f"Market found: {market.get('question')}")
            self.logger.info(f"Market ID: {market.get('condition_id')}")
            return True
        else:
            self.logger.warning("No active market found")
            return False
    
    def execute_trade(self, outcome: str, side: str) -> bool:
        """
        Execute a trade (buy or sell).
        
        Args:
            outcome: 'UP' or 'DOWN'
            side: 'BUY' or 'SELL'
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get token ID
            token_id = self.client.get_token_id(self.current_market, outcome)
            if not token_id:
                self.logger.error(f"Could not find token ID for {outcome}")
                return False
            
            # Get current price
            prices = self.client.get_current_prices(self.current_market['condition_id'])
            if not prices or outcome not in prices:
                self.logger.error(f"Could not get price for {outcome}")
                return False
            
            current_price = prices[outcome]
            
            # Calculate size based on position value
            size = self.position_value_usdc / current_price
            
            # Ensure minimum order value of $1.01 (Polymarket requirement)
            order_value = size * current_price
            if order_value < 1.01:
                size = 1.01 / current_price
                self.logger.info(f"Adjusted size to {size:.4f} shares to meet $1.01 minimum")
            
            # Place order
            order_id = self.client.place_order(
                token_id=token_id,
                side=side,
                size=size,
                price=current_price
            )
            
            if order_id:
                self.logger.info(f"Trade executed: {side} {size:.2f} {outcome} @ ${current_price:.4f}")
                return True
            else:
                self.logger.error(f"Failed to place order")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
            return False
    
    def handle_entry_signal(self, outcome: str) -> None:
        """
        Handle entry signal by opening a position.
        
        Args:
            outcome: 'UP' or 'DOWN'
        """
        self.logger.info(f"Processing entry signal for {outcome}")
        
        # Execute buy order
        if self.execute_trade(outcome, 'BUY'):
            # Get current price for tracking
            prices = self.client.get_current_prices(self.current_market['condition_id'])
            if prices and outcome in prices:
                entry_price = prices[outcome]
                size = self.position_value_usdc / entry_price
                
                # Ensure minimum order value of $1.01
                order_value = size * entry_price
                if order_value < 1.01:
                    size = 1.01 / entry_price
                    logger.info(f"Adjusted size to {size:.4f} to meet $1.01 minimum (was ${order_value:.4f})")
                
                # Update strategy
                self.strategy.enter_position(outcome, entry_price)
                
                # Update position tracker
                self.position_tracker.open_position(outcome, entry_price, size)
                
                self.logger.info(f"Successfully entered {outcome} position")
    
    def handle_exit_signal(self) -> None:
        """Handle exit signal by closing position and flipping to inverse."""
        current_position = self.strategy.current_position
        if not current_position:
            return
        
        self.logger.info(f"Processing exit signal for {current_position}")
        
        # Execute sell order for current position
        if self.execute_trade(current_position, 'SELL'):
            # Get exit price
            prices = self.client.get_current_prices(self.current_market['condition_id'])
            if prices and current_position in prices:
                exit_price = prices[current_position]
                
                # Close position in tracker
                pnl = self.position_tracker.close_position(exit_price)
                if pnl is not None:
                    self.logger.info(f"Position closed with P&L: ${pnl:.2f}")
                
                # Get inverse position from strategy
                inverse_position = self.strategy.exit_position()
                
                if inverse_position:
                    self.logger.info(f"Flipping to {inverse_position} position")
                    # Small delay to ensure order is processed
                    time.sleep(1)
                    # Enter inverse position
                    self.handle_entry_signal(inverse_position)
    
    def run_trading_cycle(self) -> None:
        """Execute one trading cycle."""
        try:
            # Get current prices
            prices = self.client.get_current_prices(self.current_market['condition_id'])
            
            if not prices:
                self.logger.warning("Failed to fetch prices")
                return
            
            # Update strategy with current prices
            self.strategy.update_prices(prices)
            
            # Log current state
            self.logger.debug(f"UP: ${prices.get('UP', 0):.4f} | DOWN: ${prices.get('DOWN', 0):.4f}")
            
            # Check for signals
            if self.strategy.current_position is None:
                # No position - check for entry
                entry_signal = self.strategy.check_entry_signal()
                if entry_signal:
                    self.handle_entry_signal(entry_signal)
            else:
                # In position - check for exit
                current_pos = self.strategy.current_position
                current_price = prices.get(current_pos, 0)
                unrealized_pnl = self.position_tracker.get_current_pnl(current_price)
                
                self.logger.debug(f"Position: {current_pos} @ ${current_price:.4f} "
                                f"(Unrealized P&L: ${unrealized_pnl:.2f})")
                
                exit_signal = self.strategy.check_exit_signal()
                if exit_signal:
                    self.handle_exit_signal()
            
            # Log statistics periodically (every 60 cycles)
            if hasattr(self, '_cycle_count'):
                self._cycle_count += 1
                if self._cycle_count % 60 == 0:
                    stats = self.position_tracker.get_statistics()
                    self.logger.info(f"Stats: {stats['total_trades']} trades, "
                                   f"${stats['total_pnl']:.2f} total P&L, "
                                   f"{stats['win_rate']:.1f}% win rate")
            else:
                self._cycle_count = 1
                
        except Exception as e:
            self.logger.error(f"Error in trading cycle: {e}", exc_info=True)
    
    def run(self) -> None:
        """Main bot loop."""
        # Find market
        if not self.find_market():
            self.logger.error("Could not find market, exiting")
            return
        
        # Check balance
        balance = self.client.get_balance()
        if balance is None or balance < self.position_value_usdc:
            self.logger.error(f"Insufficient balance. Required: ${self.position_value_usdc}, "
                            f"Available: ${balance}")
            return
        
        self.logger.info("Starting trading loop...")
        self.logger.info(f"Available balance: ${balance:.2f} USDC")
        
        # Main loop
        while self.running:
            try:
                self.run_trading_cycle()
                time.sleep(self.check_interval)
            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt received")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
                time.sleep(self.check_interval)
        
        # Shutdown
        self.logger.info("Bot stopped")
        
        # Print final statistics
        stats = self.position_tracker.get_statistics()
        self.logger.info("=" * 80)
        self.logger.info("Final Statistics:")
        self.logger.info(f"  Total Trades: {stats['total_trades']}")
        self.logger.info(f"  Total P&L: ${stats['total_pnl']:.2f}")
        self.logger.info(f"  Win Rate: {stats['win_rate']:.1f}%")
        self.logger.info(f"  Average P&L: ${stats['average_pnl']:.2f}")
        self.logger.info("=" * 80)


def main():
    """Entry point."""
    bot = PolymarketTradingBot()
    bot.run()


if __name__ == "__main__":
    main()
