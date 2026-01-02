"""
Trading strategy implementation for Polymarket Bitcoin 15min Up/Down market.

Entry Conditions:
1. Price increases 5% from its recent low, OR
2. Price exceeds $0.60 (if condition 1 hasn't been met)

Exit/Reversal Condition:
- Position price drops 5% from its recent high -> close and flip to inverse position
"""
import logging
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime


logger = logging.getLogger("PolymarketBot")


@dataclass
class PriceState:
    """Tracks price state for a single outcome (UP or DOWN)."""
    current_price: float
    low_price: float
    high_price: float
    last_update: datetime
    entry_condition_met: bool = False  # Track if 5% increase condition was met


class TradingStrategy:
    """Implements the trading strategy logic."""
    
    def __init__(self, 
                 entry_threshold_percent: float = 5.0,
                 entry_price_threshold: float = 0.60,
                 exit_reversal_percent: float = 5.0):
        """
        Initialize trading strategy.
        
        Args:
            entry_threshold_percent: Percentage increase from low to trigger entry
            entry_price_threshold: Absolute price threshold for entry
            exit_reversal_percent: Percentage drop from high to trigger exit/reversal
        """
        self.entry_threshold_percent = entry_threshold_percent
        self.entry_price_threshold = entry_price_threshold
        self.exit_reversal_percent = exit_reversal_percent
        
        # Track price states for UP and DOWN
        self.price_states: Dict[str, PriceState] = {}
        
        # Track position state
        self.current_position: Optional[str] = None  # 'UP', 'DOWN', or None
        self.position_entry_price: Optional[float] = None
        self.position_high: Optional[float] = None
        
        logger.info(f"Strategy initialized: entry_threshold={entry_threshold_percent}%, "
                   f"price_threshold=${entry_price_threshold}, "
                   f"exit_reversal={exit_reversal_percent}%")
    
    def update_prices(self, prices: Dict[str, float]) -> None:
        """
        Update current prices and track lows/highs.
        
        Args:
            prices: Dictionary with 'UP' and 'DOWN' current prices
        """
        current_time = datetime.now()
        
        for outcome in ['UP', 'DOWN']:
            if outcome not in prices:
                logger.warning(f"Missing price for {outcome}")
                continue
            
            current_price = prices[outcome]
            
            # Initialize or update price state
            if outcome not in self.price_states:
                self.price_states[outcome] = PriceState(
                    current_price=current_price,
                    low_price=current_price,
                    high_price=current_price,
                    last_update=current_time
                )
                logger.info(f"Initialized {outcome} tracking: ${current_price:.4f}")
            else:
                state = self.price_states[outcome]
                state.current_price = current_price
                state.last_update = current_time
                
                # Update low
                if current_price < state.low_price:
                    state.low_price = current_price
                    logger.debug(f"{outcome} new low: ${current_price:.4f}")
                
                # Update high
                if current_price > state.high_price:
                    state.high_price = current_price
                    logger.debug(f"{outcome} new high: ${current_price:.4f}")
        
        # Update position high if we have an active position
        if self.current_position and self.current_position in prices:
            current_pos_price = prices[self.current_position]
            if self.position_high is None or current_pos_price > self.position_high:
                self.position_high = current_pos_price
                logger.debug(f"Position {self.current_position} new high: ${self.position_high:.4f}")
    
    def check_entry_signal(self) -> Optional[str]:
        """
        Check if entry conditions are met for UP or DOWN.
        
        Returns:
            'UP', 'DOWN', or None if no entry signal
        """
        if self.current_position is not None:
            return None  # Already in a position
        
        for outcome in ['UP', 'DOWN']:
            if outcome not in self.price_states:
                continue
            
            state = self.price_states[outcome]
            
            # Condition 1: 5% increase from low
            if state.low_price > 0:
                increase_percent = ((state.current_price - state.low_price) / state.low_price) * 100
                
                if increase_percent >= self.entry_threshold_percent and not state.entry_condition_met:
                    state.entry_condition_met = True
                    logger.info(f"ENTRY SIGNAL: {outcome} increased {increase_percent:.2f}% from low "
                              f"(${state.low_price:.4f} -> ${state.current_price:.4f})")
                    return outcome
            
            # Condition 2: Price exceeds threshold (only if condition 1 hasn't been met)
            if not state.entry_condition_met and state.current_price >= self.entry_price_threshold:
                logger.info(f"ENTRY SIGNAL: {outcome} exceeded ${self.entry_price_threshold} "
                          f"(current: ${state.current_price:.4f})")
                return outcome
        
        return None
    
    def check_exit_signal(self) -> bool:
        """
        Check if exit/reversal conditions are met for current position.
        
        Returns:
            True if should exit and flip position, False otherwise
        """
        if self.current_position is None:
            return False
        
        if self.current_position not in self.price_states:
            logger.warning(f"No price state for current position {self.current_position}")
            return False
        
        state = self.price_states[self.current_position]
        
        # Check for 5% drop from position high
        if self.position_high and self.position_high > 0:
            drop_percent = ((self.position_high - state.current_price) / self.position_high) * 100
            
            if drop_percent >= self.exit_reversal_percent:
                logger.info(f"EXIT SIGNAL: {self.current_position} dropped {drop_percent:.2f}% from high "
                          f"(${self.position_high:.4f} -> ${state.current_price:.4f})")
                return True
        
        return False
    
    def enter_position(self, outcome: str, entry_price: float) -> None:
        """
        Record entering a position.
        
        Args:
            outcome: 'UP' or 'DOWN'
            entry_price: Entry price
        """
        self.current_position = outcome
        self.position_entry_price = entry_price
        self.position_high = entry_price
        logger.info(f"Entered {outcome} position at ${entry_price:.4f}")
    
    def exit_position(self) -> Optional[str]:
        """
        Record exiting current position and return the inverse position to enter.
        
        Returns:
            The inverse position to enter ('UP' or 'DOWN'), or None
        """
        if self.current_position is None:
            return None
        
        # Determine inverse position
        inverse_position = 'DOWN' if self.current_position == 'UP' else 'UP'
        
        logger.info(f"Exiting {self.current_position} position, flipping to {inverse_position}")
        
        # Reset position tracking
        self.current_position = None
        self.position_entry_price = None
        self.position_high = None
        
        return inverse_position
    
    def reset_tracking(self) -> None:
        """Reset all price tracking (useful for new market detection)."""
        self.price_states.clear()
        self.current_position = None
        self.position_entry_price = None
        self.position_high = None
        logger.info("Strategy tracking reset")
    
    def get_status(self) -> Dict:
        """
        Get current strategy status.
        
        Returns:
            Dictionary with current state information
        """
        status = {
            'current_position': self.current_position,
            'position_entry_price': self.position_entry_price,
            'position_high': self.position_high,
            'price_states': {}
        }
        
        for outcome, state in self.price_states.items():
            status['price_states'][outcome] = {
                'current': state.current_price,
                'low': state.low_price,
                'high': state.high_price,
                'entry_condition_met': state.entry_condition_met
            }
        
        return status
