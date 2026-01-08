#!/usr/bin/env python3
"""
Position Tracker for Harmonic Trading Bot
Tracks open positions, calculates PnL, monitors daily limits
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, date
import json
from pathlib import Path


class PositionTracker:
    """Track and manage trading positions"""
    
    def __init__(self, config: dict):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.max_open_positions = config.get('max_open_positions', 3)
        self.max_daily_loss_pct = config.get('max_daily_loss', 5.0)
        
        # State tracking
        self.open_positions: Dict[str, Dict] = {}
        self.daily_trades: List[Dict] = []
        self.daily_pnl = 0.0
        self.current_date = date.today()
        
        # Statistics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        
        self.logger.info("PositionTracker initialized")
    
    def add_position(self, order_result: Dict) -> bool:
        """
        Add a new position to tracking
        
        Args:
            order_result: Result from OrderExecutor.place_order()
        
        Returns:
            True if added successfully
        """
        try:
            if not order_result.get('success'):
                return False
            
            position_id = order_result['order_id']
            
            position = {
                'position_id': position_id,
                'symbol': order_result['symbol'],
                'side': order_result['side'],
                'quantity': order_result['quantity'],
                'entry_price': order_result['executed_price'],
                'stop_loss': order_result['stop_loss'],
                'take_profit': order_result['take_profit'],
                'leverage': order_result.get('leverage', 1),
                'margin_used': order_result.get('margin_used', 0),
                'entry_time': datetime.now().isoformat(),
                'status': 'open',
                'mode': order_result.get('mode', 'paper'),
                'metadata': order_result.get('metadata', {})
            }
            
            self.open_positions[position_id] = position
            self.logger.info(f"Position added: {position_id} | {position['symbol']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding position: {e}")
            return False
    
    def close_position(
        self,
        position_id: str,
        close_price: float,
        reason: str = 'manual'
    ) -> Optional[Dict]:
        """
        Close a position and calculate P&L
        
        Args:
            position_id: Position ID to close
            close_price: Closing price
            reason: Reason for closing
        
        Returns:
            Position with P&L data or None if not found
        """
        try:
            if position_id not in self.open_positions:
                self.logger.warning(f"Position not found: {position_id}")
                return None
            
            position = self.open_positions[position_id]
            
            # Calculate P&L
            entry_price = position['entry_price']
            quantity = position['quantity']
            leverage = position['leverage']
            side = position['side']
            
            if side == 'buy':
                pnl_per_unit = close_price - entry_price
            else:
                pnl_per_unit = entry_price - close_price
            
            pnl_usdt = (pnl_per_unit * quantity) * leverage
            pnl_percent = (pnl_per_unit / entry_price) * 100 * leverage
            
            # Update position
            position['close_price'] = close_price
            position['close_time'] = datetime.now().isoformat()
            position['pnl'] = pnl_usdt
            position['pnl_percent'] = pnl_percent
            position['close_reason'] = reason
            position['status'] = 'closed'
            
            # Update statistics
            self.total_trades += 1
            if pnl_usdt > 0:
                self.winning_trades += 1
            else:
                self.losing_trades += 1
            
            # Update daily P&L
            self._update_daily_pnl(pnl_usdt)
            
            # Add to daily trades
            self.daily_trades.append(position.copy())
            
            # Remove from open positions
            del self.open_positions[position_id]
            
            self.logger.info(
                f"Position closed: {position_id} | "
                f"P&L: {pnl_usdt:+.2f} USDT ({pnl_percent:+.2f}%) | "
                f"Reason: {reason}"
            )
            
            return position
            
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return None
    
    def can_open_new_position(self) -> Dict[str, any]:
        """
        Check if new position can be opened
        
        Returns:
            Dictionary with permission and reason
        """
        # Check max positions limit
        if len(self.open_positions) >= self.max_open_positions:
            return {
                'allowed': False,
                'reason': f'Max positions ({self.max_open_positions}) reached',
                'open_count': len(self.open_positions)
            }
        
        # Check daily loss limit
        daily_loss_check = self.check_daily_loss_limit(account_balance=10000)  # Will be updated with real balance
        if daily_loss_check['limit_exceeded']:
            return {
                'allowed': False,
                'reason': f"Daily loss limit exceeded: {daily_loss_check['daily_loss']:.2f} USDT",
                'daily_pnl': self.daily_pnl
            }
        
        return {
            'allowed': True,
            'open_count': len(self.open_positions),
            'daily_pnl': self.daily_pnl
        }
    
    def check_daily_loss_limit(self, account_balance: float) -> Dict:
        """
        Check if daily loss limit has been exceeded
        
        Args:
            account_balance: Current account balance
        
        Returns:
            Dictionary with limit check result
        """
        # Reset daily stats if new day
        self._check_new_day()
        
        max_loss_amount = account_balance * (self.max_daily_loss_pct / 100)
        daily_loss = abs(min(self.daily_pnl, 0))
        
        limit_exceeded = daily_loss >= max_loss_amount
        remaining = max_loss_amount - daily_loss
        
        return {
            'limit_exceeded': limit_exceeded,
            'daily_loss': round(daily_loss, 2),
            'max_loss_allowed': round(max_loss_amount, 2),
            'remaining': round(remaining, 2),
            'daily_pnl': round(self.daily_pnl, 2),
            'daily_pnl_percent': round((self.daily_pnl / account_balance) * 100, 2)
        }
    
    def get_position_by_symbol(self, symbol: str) -> Optional[Dict]:
        """Get open position for a symbol"""
        for position in self.open_positions.values():
            if position['symbol'] == symbol:
                return position
        return None
    
    def has_open_position_for_symbol(self, symbol: str) -> bool:
        """Check if there's an open position for a symbol"""
        return self.get_position_by_symbol(symbol) is not None
    
    def update_position_prices(self, current_prices: Dict[str, float]):
        """
        Update unrealized P&L for all open positions
        
        Args:
            current_prices: Dictionary of symbol -> current price
        """
        for position_id, position in self.open_positions.items():
            symbol = position['symbol']
            if symbol in current_prices:
                current_price = current_prices[symbol]
                
                # Calculate unrealized P&L
                entry_price = position['entry_price']
                quantity = position['quantity']
                leverage = position['leverage']
                side = position['side']
                
                if side == 'buy':
                    pnl_per_unit = current_price - entry_price
                else:
                    pnl_per_unit = entry_price - current_price
                
                unrealized_pnl = (pnl_per_unit * quantity) * leverage
                unrealized_pnl_pct = (pnl_per_unit / entry_price) * 100 * leverage
                
                position['current_price'] = current_price
                position['unrealized_pnl'] = unrealized_pnl
                position['unrealized_pnl_percent'] = unrealized_pnl_pct
                
                # Check if stop-loss or take-profit hit
                if side == 'buy':
                    if current_price <= position['stop_loss']:
                        position['sl_hit'] = True
                    elif current_price >= position['take_profit']:
                        position['tp_hit'] = True
                else:
                    if current_price >= position['stop_loss']:
                        position['sl_hit'] = True
                    elif current_price <= position['take_profit']:
                        position['tp_hit'] = True
    
    def get_statistics(self) -> Dict:
        """Get trading statistics"""
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': round(win_rate, 2),
            'open_positions': len(self.open_positions),
            'daily_pnl': round(self.daily_pnl, 2),
            'daily_trades_count': len(self.daily_trades)
        }
    
    def get_summary(self) -> str:
        """Get formatted summary of positions"""
        stats = self.get_statistics()
        
        summary = f"📊 <b>Position Summary</b>\n\n"
        summary += f"Open Positions: {stats['open_positions']}/{self.max_open_positions}\n"
        summary += f"Daily P&L: {stats['daily_pnl']:+.2f} USDT\n"
        summary += f"Daily Trades: {stats['daily_trades_count']}\n\n"
        summary += f"<b>Overall Stats:</b>\n"
        summary += f"Total Trades: {stats['total_trades']}\n"
        summary += f"Win Rate: {stats['win_rate']:.1f}%\n"
        summary += f"Wins: {stats['winning_trades']} | Losses: {stats['losing_trades']}"
        
        return summary
    
    def _update_daily_pnl(self, pnl: float):
        """Update daily P&L"""
        self._check_new_day()
        self.daily_pnl += pnl
    
    def _check_new_day(self):
        """Reset daily stats if new day"""
        today = date.today()
        if today != self.current_date:
            self.logger.info(
                f"New day started. Previous day P&L: {self.daily_pnl:.2f} USDT, "
                f"Trades: {len(self.daily_trades)}"
            )
            self.current_date = today
            self.daily_pnl = 0.0
            self.daily_trades = []
    
    def save_state(self, filepath: str = 'position_state.json'):
        """Save tracker state to file"""
        try:
            state = {
                'open_positions': self.open_positions,
                'daily_pnl': self.daily_pnl,
                'current_date': self.current_date.isoformat(),
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'daily_trades': self.daily_trades
            }
            
            with open(filepath, 'w') as f:
                json.dump(state, f, indent=2)
            
            self.logger.debug(f"State saved to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error saving state: {e}")
    
    def load_state(self, filepath: str = 'position_state.json'):
        """Load tracker state from file"""
        try:
            if not Path(filepath).exists():
                return False
            
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            self.open_positions = state.get('open_positions', {})
            self.daily_pnl = state.get('daily_pnl', 0.0)
            self.current_date = date.fromisoformat(state.get('current_date', date.today().isoformat()))
            self.total_trades = state.get('total_trades', 0)
            self.winning_trades = state.get('winning_trades', 0)
            self.losing_trades = state.get('losing_trades', 0)
            self.daily_trades = state.get('daily_trades', [])
            
            self.logger.info(f"State loaded from {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading state: {e}")
            return False
