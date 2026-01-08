#!/usr/bin/env python3
"""
Simple Order Executor for Paper Trading
Standalone module for any trading bot - no exchange dependency
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, Optional, List


class OrderExecutor:
    """Execute and manage paper trading orders"""

    def __init__(self, initial_balance: float = 1000, min_trade_size: float = 20):
        """
        Initialize order executor for paper trading

        Args:
            initial_balance: Starting balance in USDT
            min_trade_size: Minimum trade size in USDT
        """
        self.logger = logging.getLogger(__name__)
        self.paper_balance = initial_balance
        self.min_trade_size = min_trade_size
        self.paper_orders = []
        self.paper_positions = {}
        self.slippage = 0.001  # 0.1% slippage

        self.logger.info(f"OrderExecutor initialized with ${initial_balance:.2f} balance")

    def open_position(
        self,
        symbol: str,
        side: str,  # 'buy' for long, 'sell' for short
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        leverage: int = 10,
        position_size_usd: Optional[float] = None
    ) -> Optional[str]:
        """
        Open a new paper trading position

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            side: 'buy' for long, 'sell' for short
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            leverage: Leverage to use
            position_size_usd: Position size in USDT (if None, uses min_trade_size)

        Returns:
            Position ID if successful, None otherwise
        """
        try:
            # Use min trade size if not specified
            if position_size_usd is None:
                position_size_usd = self.min_trade_size

            # Calculate quantity
            quantity = position_size_usd / entry_price

            # Calculate margin required
            margin_required = position_size_usd / leverage

            # Check balance
            if margin_required > self.paper_balance:
                self.logger.warning(
                    f"Insufficient balance: need ${margin_required:.2f}, have ${self.paper_balance:.2f}"
                )
                return None

            # Simulate slippage for market orders
            slippage_amount = entry_price * self.slippage
            executed_price = entry_price + slippage_amount if side == 'buy' else entry_price - slippage_amount

            # Generate position ID
            position_id = f"PAPER_{int(time.time() * 1000)}_{symbol.replace('/', '_')}"

            # Create position
            position = {
                'position_id': position_id,
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'entry_price': executed_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'leverage': leverage,
                'position_value': position_size_usd,
                'margin_used': margin_required,
                'status': 'open',
                'open_time': datetime.now().isoformat(),
                'mode': 'paper'
            }

            # Update balance
            self.paper_balance -= margin_required

            # Store position
            self.paper_positions[position_id] = position
            self.paper_orders.append(position)

            self.logger.info(
                f"📝 PAPER POSITION OPENED: {side.upper()} {quantity:.6f} {symbol} @ {executed_price:.6f} "
                f"| SL: {stop_loss:.6f} | TP: {take_profit:.6f} | Leverage: {leverage}x | "
                f"Balance: ${self.paper_balance:.2f}"
            )

            return position_id

        except Exception as e:
            self.logger.error(f"Error opening position: {e}")
            return None

    def close_position(self, position_id: str, close_price: float, reason: str = 'manual') -> Optional[Dict]:
        """
        Close an open position

        Args:
            position_id: Position ID to close
            close_price: Closing price
            reason: Reason for closing (manual, tp_hit, sl_hit)

        Returns:
            Close result dictionary or None
        """
        try:
            if position_id not in self.paper_positions:
                self.logger.warning(f"Position not found: {position_id}")
                return None

            position = self.paper_positions[position_id]

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

            # Return margin + profit/loss
            margin_returned = position['margin_used']
            self.paper_balance += margin_returned + pnl_usdt

            # Update position
            position['close_price'] = close_price
            position['close_time'] = datetime.now().isoformat()
            position['pnl'] = pnl_usdt
            position['pnl_percent'] = pnl_percent
            position['close_reason'] = reason
            position['status'] = 'closed'

            # Remove from active positions
            del self.paper_positions[position_id]

            emoji = "📈" if pnl_usdt >= 0 else "📉"
            self.logger.info(
                f"{emoji} PAPER POSITION CLOSED: {position['symbol']} | "
                f"P&L: {pnl_usdt:+.2f} USDT ({pnl_percent:+.2f}%) | "
                f"Reason: {reason} | Balance: ${self.paper_balance:.2f}"
            )

            return {
                'success': True,
                'position_id': position_id,
                'symbol': position['symbol'],
                'pnl': pnl_usdt,
                'pnl_percent': pnl_percent,
                'balance': self.paper_balance,
                'reason': reason
            }

        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return None

    def get_open_positions(self) -> List[Dict]:
        """Get all open positions"""
        return list(self.paper_positions.values())

    def get_balance(self) -> float:
        """Get current balance"""
        return self.paper_balance

    def check_positions_for_close(self, current_prices: Dict[str, float]) -> List[Dict]:
        """
        Check all open positions against current prices for TP/SL hits

        Args:
            current_prices: Dictionary of symbol -> current price

        Returns:
            List of closed positions
        """
        closed_positions = []

        for position_id, position in list(self.paper_positions.items()):
            symbol = position['symbol']

            if symbol not in current_prices:
                continue

            current_price = current_prices[symbol]
            side = position['side']
            sl = position['stop_loss']
            tp = position['take_profit']

            # Check if TP or SL hit
            close_reason = None

            if side == 'buy':
                if current_price <= sl:
                    close_reason = 'sl_hit'
                elif current_price >= tp:
                    close_reason = 'tp_hit'
            else:  # sell/short
                if current_price >= sl:
                    close_reason = 'sl_hit'
                elif current_price <= tp:
                    close_reason = 'tp_hit'

            if close_reason:
                result = self.close_position(position_id, current_price, close_reason)
                if result:
                    closed_positions.append(result)

        return closed_positions

    def save_state(self, filepath: str = 'order_executor_state.json'):
        """Save executor state to file"""
        try:
            state = {
                'paper_balance': self.paper_balance,
                'paper_positions': self.paper_positions,
                'paper_orders': self.paper_orders[-100:]  # Keep last 100 orders
            }

            with open(filepath, 'w') as f:
                json.dump(state, f, indent=2)

            self.logger.debug(f"State saved to {filepath}")

        except Exception as e:
            self.logger.error(f"Error saving state: {e}")

    def load_state(self, filepath: str = 'order_executor_state.json'):
        """Load executor state from file"""
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)

            self.paper_balance = state.get('paper_balance', self.paper_balance)
            self.paper_positions = state.get('paper_positions', {})
            self.paper_orders = state.get('paper_orders', [])

            self.logger.info(
                f"State loaded: Balance=${self.paper_balance:.2f}, "
                f"Open positions={len(self.paper_positions)}"
            )
            return True

        except FileNotFoundError:
            self.logger.info("No state file found, starting fresh")
            return False
        except Exception as e:
            self.logger.error(f"Error loading state: {e}")
            return False
