"""
Position tracking and management for the Polymarket trading bot.
"""
import logging
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict
from datetime import datetime
import json


logger = logging.getLogger("PolymarketBot")


@dataclass
class Position:
    """Represents a trading position."""
    outcome: str  # 'UP' or 'DOWN'
    entry_price: float
    size: float  # Number of shares
    entry_time: datetime
    entry_order_id: Optional[str] = None
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    exit_order_id: Optional[str] = None
    pnl: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['entry_time'] = self.entry_time.isoformat()
        if self.exit_time:
            data['exit_time'] = self.exit_time.isoformat()
        return data


class PositionTracker:
    """Tracks current and historical positions."""
    
    def __init__(self, position_history_file: str = "position_history.json"):
        """
        Initialize position tracker.
        
        Args:
            position_history_file: File to store position history
        """
        self.current_position: Optional[Position] = None
        self.position_history: List[Position] = []
        self.position_history_file = position_history_file
        
        # Load existing history if available
        self._load_history()
        
        logger.info("Position tracker initialized")
    
    def open_position(self, 
                     outcome: str, 
                     entry_price: float, 
                     size: float,
                     order_id: Optional[str] = None) -> None:
        """
        Open a new position.
        
        Args:
            outcome: 'UP' or 'DOWN'
            entry_price: Entry price per share
            size: Number of shares
            order_id: Order ID from exchange
        """
        if self.current_position is not None:
            logger.warning(f"Opening new position while one exists: {self.current_position.outcome}")
        
        self.current_position = Position(
            outcome=outcome,
            entry_price=entry_price,
            size=size,
            entry_time=datetime.now(),
            entry_order_id=order_id
        )
        
        logger.info(f"Opened {outcome} position: {size} shares @ ${entry_price:.4f} "
                   f"(total: ${entry_price * size:.2f})")
    
    def close_position(self, 
                      exit_price: float,
                      order_id: Optional[str] = None) -> Optional[float]:
        """
        Close the current position.
        
        Args:
            exit_price: Exit price per share
            order_id: Order ID from exchange
        
        Returns:
            Profit/loss in USDC, or None if no position
        """
        if self.current_position is None:
            logger.warning("Attempted to close position but none exists")
            return None
        
        # Calculate P&L
        pnl = (exit_price - self.current_position.entry_price) * self.current_position.size
        
        # Update position
        self.current_position.exit_price = exit_price
        self.current_position.exit_time = datetime.now()
        self.current_position.exit_order_id = order_id
        self.current_position.pnl = pnl
        
        # Log the close
        duration = (self.current_position.exit_time - self.current_position.entry_time).total_seconds()
        logger.info(f"Closed {self.current_position.outcome} position: "
                   f"{self.current_position.size} shares @ ${exit_price:.4f} "
                   f"(P&L: ${pnl:.2f}, Duration: {duration:.0f}s)")
        
        # Add to history
        self.position_history.append(self.current_position)
        self._save_history()
        
        # Clear current position
        self.current_position = None
        
        return pnl
    
    def get_current_pnl(self, current_price: float) -> Optional[float]:
        """
        Calculate current unrealized P&L.
        
        Args:
            current_price: Current market price
        
        Returns:
            Unrealized P&L in USDC, or None if no position
        """
        if self.current_position is None:
            return None
        
        return (current_price - self.current_position.entry_price) * self.current_position.size
    
    def get_position_info(self) -> Optional[Dict]:
        """
        Get current position information.
        
        Returns:
            Dictionary with position details, or None if no position
        """
        if self.current_position is None:
            return None
        
        return {
            'outcome': self.current_position.outcome,
            'entry_price': self.current_position.entry_price,
            'size': self.current_position.size,
            'entry_time': self.current_position.entry_time.isoformat(),
            'entry_order_id': self.current_position.entry_order_id,
            'duration_seconds': (datetime.now() - self.current_position.entry_time).total_seconds()
        }
    
    def get_statistics(self) -> Dict:
        """
        Get trading statistics from history.
        
        Returns:
            Dictionary with statistics
        """
        if not self.position_history:
            return {
                'total_trades': 0,
                'total_pnl': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'average_pnl': 0
            }
        
        total_trades = len(self.position_history)
        total_pnl = sum(p.pnl for p in self.position_history if p.pnl is not None)
        winning_trades = sum(1 for p in self.position_history if p.pnl and p.pnl > 0)
        losing_trades = sum(1 for p in self.position_history if p.pnl and p.pnl < 0)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        average_pnl = total_pnl / total_trades if total_trades > 0 else 0
        
        return {
            'total_trades': total_trades,
            'total_pnl': total_pnl,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'average_pnl': average_pnl
        }
    
    def _save_history(self) -> None:
        """Save position history to file."""
        try:
            history_data = [p.to_dict() for p in self.position_history]
            with open(self.position_history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
            logger.debug(f"Saved position history: {len(history_data)} positions")
        except Exception as e:
            logger.error(f"Failed to save position history: {e}")
    
    def _load_history(self) -> None:
        """Load position history from file."""
        try:
            with open(self.position_history_file, 'r') as f:
                history_data = json.load(f)
            
            for data in history_data:
                # Convert datetime strings back to datetime objects
                data['entry_time'] = datetime.fromisoformat(data['entry_time'])
                if data.get('exit_time'):
                    data['exit_time'] = datetime.fromisoformat(data['exit_time'])
                
                self.position_history.append(Position(**data))
            
            logger.info(f"Loaded position history: {len(self.position_history)} positions")
        except FileNotFoundError:
            logger.info("No existing position history found")
        except Exception as e:
            logger.error(f"Failed to load position history: {e}")
