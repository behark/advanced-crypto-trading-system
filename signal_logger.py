#!/usr/bin/env python3
"""
Signal Logger - Logs trading signals to JSON file for tracker monitoring
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import os


class SignalLogger:
    """Log trading signals to JSON file for signal_tracker.py monitoring"""

    def __init__(self, signals_file: str = 'signals_log.json'):
        """
        Initialize signal logger

        Args:
            signals_file: Path to signals log file
        """
        self.logger = logging.getLogger(__name__)
        self.signals_file = signals_file
        self.signals = []

        # Load existing signals
        self._load_signals()

    def _load_signals(self):
        """Load existing signals from file"""
        try:
            if os.path.exists(self.signals_file):
                with open(self.signals_file, 'r') as f:
                    self.signals = json.load(f)
                    if not isinstance(self.signals, list):
                        self.signals = [self.signals]
                self.logger.info(f"Loaded {len(self.signals)} existing signals")
            else:
                self.signals = []
                self._save_signals()
        except Exception as e:
            self.logger.error(f"Error loading signals: {e}")
            self.signals = []

    def _save_signals(self):
        """Save signals to file"""
        try:
            with open(self.signals_file, 'w') as f:
                json.dump(self.signals, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving signals: {e}")

    def log_signal(
        self,
        symbol: str,
        direction: str,  # 'LONG' or 'SHORT'
        entry: float,
        stop_loss: float,
        take_profit: float,
        position_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Log a trading signal

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            direction: 'LONG' or 'SHORT'
            entry: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            position_id: Position ID from order executor
            metadata: Additional signal metadata

        Returns:
            Signal ID
        """
        try:
            # Create unique signal ID
            timestamp = datetime.now().isoformat()
            signal_id = f"{timestamp}_{symbol}_{direction}"

            # Build signal data
            signal_data = {
                "signal_id": signal_id,
                "timestamp": timestamp,
                "symbol": symbol,
                "direction": direction,
                "entry": entry,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "status": "pending",
                "position_id": position_id
            }

            # Add metadata if provided
            if metadata:
                signal_data["metadata"] = metadata

            # Add to signals list
            self.signals.append(signal_data)

            # Keep only last 1000 signals to prevent file bloat
            if len(self.signals) > 1000:
                self.signals = self.signals[-1000:]

            # Save to file
            self._save_signals()

            self.logger.info(f"Signal logged: {signal_id}")

            return signal_id

        except Exception as e:
            self.logger.error(f"Error logging signal: {e}")
            return ""

    def update_signal_status(self, signal_id: str, status: str, result: Optional[Dict] = None):
        """
        Update signal status

        Args:
            signal_id: Signal ID
            status: New status (e.g., 'filled', 'tp_hit', 'sl_hit', 'cancelled')
            result: Additional result data
        """
        try:
            for signal in self.signals:
                if signal.get('signal_id') == signal_id:
                    signal['status'] = status
                    signal['updated_at'] = datetime.now().isoformat()

                    if result:
                        signal['result'] = result

                    self._save_signals()
                    self.logger.info(f"Signal {signal_id} updated to {status}")
                    return True

            self.logger.warning(f"Signal {signal_id} not found for update")
            return False

        except Exception as e:
            self.logger.error(f"Error updating signal: {e}")
            return False

    def get_pending_signals(self) -> List[Dict]:
        """Get all pending signals"""
        return [s for s in self.signals if s.get('status') == 'pending']

    def get_recent_signals(self, limit: int = 10) -> List[Dict]:
        """Get recent signals"""
        return self.signals[-limit:]

    def cleanup_old_signals(self, days: int = 7):
        """Remove signals older than specified days"""
        try:
            from datetime import timedelta

            cutoff_time = datetime.now() - timedelta(days=days)
            original_count = len(self.signals)

            self.signals = [
                s for s in self.signals
                if datetime.fromisoformat(s['timestamp']) > cutoff_time
            ]

            removed_count = original_count - len(self.signals)

            if removed_count > 0:
                self._save_signals()
                self.logger.info(f"Cleaned up {removed_count} old signals")

        except Exception as e:
            self.logger.error(f"Error cleaning up signals: {e}")
