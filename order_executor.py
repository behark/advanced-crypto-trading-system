#!/usr/bin/env python3
"""
Order Executor for Harmonic Trading Bot
Handles order placement, modification, and cancellation on Bybit
Supports both paper trading (simulation) and live trading
"""

import logging
import time
from typing import Dict, Optional, List
from datetime import datetime
import json
from pathlib import Path


class OrderExecutor:
    """Execute and manage trading orders"""
    
    def __init__(self, exchange_client, config: dict, mode: str = 'paper'):
        """
        Initialize order executor
        
        Args:
            exchange_client: CCXT exchange instance
            config: Trading configuration
            mode: 'paper' for simulation, 'live' for real trading
        """
        self.logger = logging.getLogger(__name__)
        self.exchange = exchange_client
        self.config = config
        self.mode = mode.lower()
        self.order_type = config.get('order_type', 'limit')
        self.slippage = config.get('slippage', 0.1) / 100  # Convert % to decimal
        
        # Paper trading state
        self.paper_balance = 10000.0  # Starting paper balance
        self.paper_orders = []
        self.paper_positions = {}
        
        self.logger.info(f"OrderExecutor initialized in {self.mode.upper()} mode")
    
    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        leverage: int = 1,
        metadata: dict = None
    ) -> Dict:
        """
        Place a new order with stop-loss and take-profit
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT:USDT')
            side: 'buy' for long, 'sell' for short
            quantity: Order quantity in base currency
            entry_price: Target entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            leverage: Leverage to use
            metadata: Additional data to store with order
        
        Returns:
            Order result dictionary
        """
        try:
            if self.mode == 'paper':
                return self._place_paper_order(
                    symbol, side, quantity, entry_price, 
                    stop_loss, take_profit, leverage, metadata
                )
            else:
                return self._place_live_order(
                    symbol, side, quantity, entry_price,
                    stop_loss, take_profit, leverage, metadata
                )
                
        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            return {
                'success': False,
                'error': str(e),
                'symbol': symbol,
                'side': side
            }
    
    def _place_paper_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        leverage: int,
        metadata: dict
    ) -> Dict:
        """Simulate order placement for paper trading"""
        
        # Generate order ID
        order_id = f"PAPER_{int(time.time() * 1000)}"
        
        # Calculate order value
        position_value = quantity * entry_price
        margin_required = position_value / leverage
        
        # Check paper balance
        if margin_required > self.paper_balance:
            self.logger.warning(f"Insufficient paper balance: {self.paper_balance:.2f} USDT")
            return {
                'success': False,
                'error': 'Insufficient balance',
                'required': margin_required,
                'available': self.paper_balance
            }
        
        # Simulate slippage for market orders
        if self.order_type == 'market':
            slippage_amount = entry_price * self.slippage
            executed_price = entry_price + slippage_amount if side == 'buy' else entry_price - slippage_amount
        else:
            executed_price = entry_price
        
        # Create paper order
        order = {
            'order_id': order_id,
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'entry_price': executed_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'leverage': leverage,
            'position_value': position_value,
            'margin_used': margin_required,
            'status': 'filled',
            'timestamp': datetime.now().isoformat(),
            'mode': 'paper',
            'metadata': metadata or {}
        }
        
        # Update paper balance
        self.paper_balance -= margin_required
        
        # Store order
        self.paper_orders.append(order)
        self.paper_positions[order_id] = order
        
        self.logger.info(
            f"📝 PAPER ORDER: {side.upper()} {quantity} {symbol} @ {executed_price:.6f} "
            f"| SL: {stop_loss:.6f} | TP: {take_profit:.6f} | Leverage: {leverage}x"
        )
        
        return {
            'success': True,
            'order_id': order_id,
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'executed_price': executed_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'margin_used': margin_required,
            'balance_remaining': self.paper_balance,
            'mode': 'paper'
        }
    
    def _place_live_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        leverage: int,
        metadata: dict
    ) -> Dict:
        """Place real order on Bybit"""
        
        try:
            # Convert symbol for linear perpetuals (BTC/USDT -> BTC/USDT:USDT)
            # This is required for Bybit linear contracts
            if ':' not in symbol and '/USDT' in symbol:
                perpetual_symbol = f"{symbol}:USDT"
            else:
                perpetual_symbol = symbol

            # Set leverage first
            self.exchange.set_leverage(leverage, perpetual_symbol)
            self.logger.info(f"Set leverage to {leverage}x for {perpetual_symbol}")
            
            # Place main order
            if self.order_type == 'market':
                order = self.exchange.create_market_order(perpetual_symbol, side, quantity)
            else:
                # Limit order
                order = self.exchange.create_limit_order(perpetual_symbol, side, quantity, entry_price)
            
            order_id = order['id']
            filled_price = order.get('average') or order.get('price') or entry_price
            
            self.logger.info(f"Order placed: {order_id} | {side.upper()} {quantity} {perpetual_symbol} @ {filled_price}")
            
            # Place stop-loss order (Bybit format)
            try:
                sl_side = 'sell' if side == 'buy' else 'buy'
                sl_order = self.exchange.create_order(
                    symbol=perpetual_symbol,
                    type='market',
                    side=sl_side,
                    amount=quantity,
                    params={
                        'triggerPrice': stop_loss,
                        'triggerBy': 'LastPrice',
                        'reduceOnly': True
                    }
                )
                self.logger.info(f"Stop-loss set at {stop_loss}")
            except Exception as e:
                self.logger.error(f"Failed to set stop-loss: {e}")
                import traceback
                self.logger.debug(traceback.format_exc())
            
            # Place take-profit order
            try:
                tp_side = 'sell' if side == 'buy' else 'buy'
                tp_order = self.exchange.create_order(
                    symbol=perpetual_symbol,
                    type='limit',
                    side=tp_side,
                    amount=quantity,
                    price=take_profit,
                    params={'reduceOnly': True}
                )
                self.logger.info(f"Take-profit set at {take_profit}")
            except Exception as e:
                self.logger.error(f"Failed to set take-profit: {e}")
            
            return {
                'success': True,
                'order_id': order_id,
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'executed_price': filled_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'leverage': leverage,
                'mode': 'live',
                'exchange_response': order
            }
            
        except Exception as e:
            self.logger.error(f"Live order failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'symbol': symbol,
                'side': side
            }
    
    def close_position(self, position_id: str, current_price: float, reason: str = 'manual') -> Dict:
        """
        Close an open position
        
        Args:
            position_id: Order/position ID
            current_price: Current market price
            reason: Reason for closing (manual, sl_hit, tp_hit, daily_limit)
        
        Returns:
            Close result dictionary
        """
        try:
            if self.mode == 'paper':
                return self._close_paper_position(position_id, current_price, reason)
            else:
                return self._close_live_position(position_id, current_price, reason)
                
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return {'success': False, 'error': str(e)}
    
    def _close_paper_position(self, position_id: str, current_price: float, reason: str) -> Dict:
        """Close paper trading position"""
        
        if position_id not in self.paper_positions:
            return {'success': False, 'error': 'Position not found'}
        
        position = self.paper_positions[position_id]
        
        # Calculate P&L
        entry_price = position['entry_price']
        quantity = position['quantity']
        leverage = position['leverage']
        side = position['side']
        
        if side == 'buy':
            pnl_per_unit = current_price - entry_price
        else:
            pnl_per_unit = entry_price - current_price
        
        pnl_usdt = (pnl_per_unit * quantity) * leverage
        pnl_percent = (pnl_per_unit / entry_price) * 100 * leverage
        
        # Return margin + profit/loss
        margin_returned = position['margin_used']
        self.paper_balance += margin_returned + pnl_usdt
        
        # Mark position as closed
        position['status'] = 'closed'
        position['close_price'] = current_price
        position['close_time'] = datetime.now().isoformat()
        position['pnl'] = pnl_usdt
        position['pnl_percent'] = pnl_percent
        position['close_reason'] = reason
        
        # Remove from active positions
        del self.paper_positions[position_id]
        
        emoji = "📈" if pnl_usdt >= 0 else "📉"
        self.logger.info(
            f"{emoji} PAPER POSITION CLOSED: {position['symbol']} | "
            f"P&L: {pnl_usdt:+.2f} USDT ({pnl_percent:+.2f}%) | "
            f"Reason: {reason} | Balance: {self.paper_balance:.2f} USDT"
        )
        
        return {
            'success': True,
            'position_id': position_id,
            'symbol': position['symbol'],
            'side': side,
            'entry_price': entry_price,
            'close_price': current_price,
            'pnl': pnl_usdt,
            'pnl_percent': pnl_percent,
            'balance': self.paper_balance,
            'reason': reason,
            'mode': 'paper'
        }
    
    def _close_live_position(self, position_id: str, current_price: float, reason: str) -> Dict:
        """Close live position on exchange"""
        # Implementation for live trading
        # This would use exchange.close_position() or create opposite order
        self.logger.warning("Live position closing not yet implemented")
        return {'success': False, 'error': 'Live trading not implemented'}
    
    def get_open_positions(self) -> List[Dict]:
        """Get all open positions"""
        if self.mode == 'paper':
            return list(self.paper_positions.values())
        else:
            try:
                return self.exchange.fetch_positions()
            except Exception as e:
                self.logger.error(f"Error fetching positions: {e}")
                return []
    
    def get_balance(self) -> float:
        """Get available balance"""
        if self.mode == 'paper':
            return self.paper_balance
        else:
            try:
                balance = self.exchange.fetch_balance()
                return balance.get('USDT', {}).get('free', 0)
            except Exception as e:
                self.logger.error(f"Error fetching balance: {e}")
                return 0
    
    def update_paper_balance(self, amount: float):
        """Manually update paper balance (for testing)"""
        if self.mode == 'paper':
            self.paper_balance = amount
            self.logger.info(f"Paper balance updated to {amount:.2f} USDT")
