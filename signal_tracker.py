#!/usr/bin/env python3
"""
Signal Tracker - Monitor TP/SL hits for trading signals
Lightweight tracker for bot_diy and bot_advanced_fixed
"""

import json
import ccxt
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SignalTracker:
    """Track trading signals and detect TP/SL hits"""

    def __init__(self,
                 signals_file: str,
                 tracking_file: str,
                 telegram_token: str,
                 telegram_chat_id: str,
                 exchange_name: str = 'mexc',
                 bot_name: str = 'Trading Bot'):
        """
        Initialize Signal Tracker

        Args:
            signals_file: Path to signals_log.json
            tracking_file: Path to save tracking results
            telegram_token: Telegram bot token
            telegram_chat_id: Telegram chat ID
            exchange_name: Exchange name (mexc, bybit, etc.)
            bot_name: Name for notifications
        """
        self.signals_file = signals_file
        self.tracking_file = tracking_file
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.bot_name = bot_name

        # Initialize exchange
        try:
            if exchange_name.lower() == 'mexc':
                self.exchange = ccxt.mexc()
            elif exchange_name.lower() == 'bybit':
                self.exchange = ccxt.bybit()
            elif exchange_name.lower() == 'binance':
                self.exchange = ccxt.binance()
            else:
                self.exchange = ccxt.mexc()  # Default
            logger.info(f"✅ Connected to {exchange_name}")
        except Exception as e:
            logger.error(f"Exchange connection error: {e}")
            self.exchange = None

        # Load tracking state
        self.tracking_data = self._load_tracking_data()

        # Statistics
        self.stats = {
            'total_signals': 0,
            'tp_hit': 0,
            'sl_hit': 0,
            'pending': 0,
            'expired': 0,
            'win_rate': 0.0,
            'total_pnl_percent': 0.0
        }

    def _load_tracking_data(self) -> Dict:
        """Load existing tracking data"""
        try:
            if os.path.exists(self.tracking_file):
                with open(self.tracking_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load tracking data: {e}")

        return {
            'tracked_signals': {},
            'completed': [],
            'statistics': {}
        }

    def _save_tracking_data(self):
        """Save tracking data to file"""
        try:
            with open(self.tracking_file, 'w') as f:
                json.dump(self.tracking_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving tracking data: {e}")

    def load_signals(self) -> List[Dict]:
        """Load signals from signals log"""
        try:
            with open(self.signals_file, 'r') as f:
                signals = json.load(f)

            if not isinstance(signals, list):
                signals = [signals]

            logger.info(f"📊 Loaded {len(signals)} signals from {self.signals_file}")
            return signals

        except Exception as e:
            logger.error(f"Error loading signals: {e}")
            return []

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Fetch current price from exchange"""
        try:
            # Normalize symbol format
            if '/' not in symbol:
                symbol = f"{symbol}/USDT"

            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']

        except Exception as e:
            logger.debug(f"Could not fetch price for {symbol}: {e}")
            return None

    def check_signal(self, signal: Dict) -> Optional[Dict]:
        """
        Check if signal hit TP or SL

        Returns:
            Dict with result if TP/SL hit, None otherwise
        """
        try:
            # Extract signal data
            timestamp = signal.get('timestamp', '')
            symbol = signal.get('symbol', '')
            direction = signal.get('direction', signal.get('action', signal.get('signal', ''))).upper()
            
            # Handle nested fib_levels structure (bot3) or flat structure (bot1, bot2)
            fib_levels = signal.get('fib_levels', {})
            entry = float(fib_levels.get('entry', 0) or signal.get('entry', signal.get('entry_price', 0)))
            sl = float(fib_levels.get('sl', 0) or signal.get('sl', signal.get('stop_loss', 0)))
            tp = float(fib_levels.get('tp', 0) or signal.get('tp', signal.get('take_profit', signal.get('take_profit_1', 0))))
            
            # Normalize direction for bot3 (bullish/bearish -> LONG/SHORT)
            if direction == 'BULLISH':
                direction = 'LONG'
            elif direction == 'BEARISH':
                direction = 'SHORT' 

            # Create unique signal ID
            signal_id = f"{timestamp}_{symbol}_{direction}"

            # Skip if already tracked
            if signal_id in self.tracking_data['tracked_signals']:
                return None

            # Skip if no SL/TP
            if not sl or not tp or not entry:
                return None

            # Skip old signals (older than 7 days)
            try:
                if isinstance(timestamp, str):
                    if 'T' in timestamp:  # ISO format
                        signal_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:  # Custom format
                        signal_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                else:
                    signal_time = datetime.fromtimestamp(float(timestamp))

                age = datetime.now() - signal_time.replace(tzinfo=None)
                if age > timedelta(days=7):
                    return None
            except:
                pass  # If timestamp parsing fails, still process

            # Get current price
            current_price = self.get_current_price(symbol)
            if not current_price:
                return None

            # Check if TP or SL hit
            result = None

            if direction in ['LONG', 'BUY']:
                if current_price >= tp:
                    # Take profit hit!
                    pnl_percent = ((tp - entry) / entry) * 100
                    result = {
                        'signal_id': signal_id,
                        'symbol': symbol,
                        'direction': direction,
                        'entry': entry,
                        'exit': current_price,
                        'sl': sl,
                        'tp': tp,
                        'outcome': 'TP_HIT',
                        'pnl_percent': pnl_percent,
                        'timestamp': timestamp,
                        'close_time': datetime.now().isoformat()
                    }
                elif current_price <= sl:
                    # Stop loss hit
                    pnl_percent = ((sl - entry) / entry) * 100
                    result = {
                        'signal_id': signal_id,
                        'symbol': symbol,
                        'direction': direction,
                        'entry': entry,
                        'exit': current_price,
                        'sl': sl,
                        'tp': tp,
                        'outcome': 'SL_HIT',
                        'pnl_percent': pnl_percent,
                        'timestamp': timestamp,
                        'close_time': datetime.now().isoformat()
                    }

            elif direction in ['SHORT', 'SELL']:
                if current_price <= tp:
                    # Take profit hit!
                    pnl_percent = ((entry - tp) / entry) * 100
                    result = {
                        'signal_id': signal_id,
                        'symbol': symbol,
                        'direction': direction,
                        'entry': entry,
                        'exit': current_price,
                        'sl': sl,
                        'tp': tp,
                        'outcome': 'TP_HIT',
                        'pnl_percent': pnl_percent,
                        'timestamp': timestamp,
                        'close_time': datetime.now().isoformat()
                    }
                elif current_price >= sl:
                    # Stop loss hit
                    pnl_percent = ((entry - sl) / entry) * 100
                    result = {
                        'signal_id': signal_id,
                        'symbol': symbol,
                        'direction': direction,
                        'entry': entry,
                        'exit': current_price,
                        'sl': sl,
                        'tp': tp,
                        'outcome': 'SL_HIT',
                        'pnl_percent': pnl_percent,
                        'timestamp': timestamp,
                        'close_time': datetime.now().isoformat()
                    }

            if result:
                # Mark as tracked
                self.tracking_data['tracked_signals'][signal_id] = {
                    'tracked_at': datetime.now().isoformat(),
                    'outcome': result['outcome']
                }

                # Add to completed
                self.tracking_data['completed'].append(result)

                # Save
                self._save_tracking_data()

                logger.info(f"🎯 {result['outcome']}: {symbol} {direction}")

            return result

        except Exception as e:
            logger.error(f"Error checking signal: {e}")
            return None

    def send_telegram_notification(self, result: Dict):
        """Send Telegram notification for TP/SL hit"""
        try:
            signal_id = result.get('signal_id', 'N/A')
            symbol = result['symbol']
            direction = result['direction']
            entry = result['entry']
            exit_price = result['exit']
            outcome = result['outcome']
            pnl_percent = result['pnl_percent']

            # Extract date from signal_id (format: "2025-12-06T03:10:15.123456_LAB/USDT_LONG")
            signal_date = "N/A"
            try:
                if '_' in signal_id:
                    timestamp_part = signal_id.split('_')[0]
                    if 'T' in timestamp_part:
                        # ISO format
                        dt = datetime.fromisoformat(timestamp_part.replace('Z', '+00:00'))
                        signal_date = dt.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        # Already in correct format
                        signal_date = timestamp_part
            except Exception as e:
                logger.debug(f"Could not extract signal date: {e}")

            # Determine emoji and title
            if outcome == 'TP_HIT':
                emoji = "🎯✅"
                title = "TAKE PROFIT HIT"
            else:  # SL_HIT
                emoji = "🛑❌"
                title = "STOP LOSS HIT"

            # Get performance statistics
            stats = self.get_statistics()

            # Build message
            msg = f"{emoji} <b>{self.bot_name} - {title}</b> {emoji}\n\n"
            msg += f"🆔 {signal_date}_{symbol}_{direction}\n\n"
            msg += f"📊 <b>Symbol:</b> {symbol}\n"
            msg += f"📍 <b>Direction:</b> {direction}\n"
            msg += f"💰 <b>Entry:</b> {entry:.6f}\n"
            msg += f"🏁 <b>Exit:</b> {exit_price:.6f}\n\n"
            msg += f"📈 <b>P&amp;L:</b> {pnl_percent:+.2f}%\n\n"
            msg += f"📊 <b>Performance Stats:</b>\n"
            msg += f"Win Rate: {stats['win_rate']:.1f}%\n"
            msg += f"TP Hits: {stats['tp_hit']} | SL Hits: {stats['sl_hit']}\n"
            msg += f"Total P&amp;L: {stats['total_pnl_percent']:+.2f}%\n\n"
            msg += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            # Send via Telegram
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                'chat_id': self.telegram_chat_id,
                'text': msg,
                'parse_mode': 'HTML'
            }

            response = requests.post(url, data=data, timeout=10)

            if response.ok:
                logger.info(f"✅ Telegram notification sent for {symbol}")
            else:
                logger.warning(f"❌ Telegram failed: {response.text}")

        except Exception as e:
            logger.error(f"Error sending Telegram: {e}")

    def get_statistics(self) -> Dict:
        """Calculate performance statistics"""
        completed = self.tracking_data.get('completed', [])

        if not completed:
            return {
                'total_signals': 0,
                'tp_hit': 0,
                'sl_hit': 0,
                'win_rate': 0.0,
                'total_pnl_percent': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0
            }

        tp_count = sum(1 for r in completed if r['outcome'] == 'TP_HIT')
        sl_count = sum(1 for r in completed if r['outcome'] == 'SL_HIT')
        total = len(completed)

        win_rate = (tp_count / total * 100) if total > 0 else 0.0

        total_pnl = sum(r.get('pnl_percent', 0) for r in completed)

        wins = [r['pnl_percent'] for r in completed if r['outcome'] == 'TP_HIT']
        losses = [r['pnl_percent'] for r in completed if r['outcome'] == 'SL_HIT']

        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0

        return {
            'total_signals': total,
            'tp_hit': tp_count,
            'sl_hit': sl_count,
            'win_rate': win_rate,
            'total_pnl_percent': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss
        }

    def monitor_signals(self, check_interval: int = 60):
        """
        Main monitoring loop

        Args:
            check_interval: Seconds between checks
        """
        logger.info(f"🚀 Starting Signal Tracker for {self.bot_name}")
        logger.info(f"📁 Monitoring: {self.signals_file}")
        logger.info(f"⏱️  Check interval: {check_interval}s")

        while True:
            try:
                # Load signals
                signals = self.load_signals()

                if not signals:
                    logger.debug("No signals to process")
                    time.sleep(check_interval)
                    continue

                # Check each signal
                hits_count = 0
                for signal in signals:
                    result = self.check_signal(signal)

                    if result:
                        # Send notification
                        self.send_telegram_notification(result)
                        hits_count += 1

                        # Small delay between notifications
                        time.sleep(2)

                if hits_count > 0:
                    logger.info(f"✅ Processed {hits_count} TP/SL hits")

                # Wait before next check
                time.sleep(check_interval)

            except KeyboardInterrupt:
                logger.info("🛑 Tracker stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(check_interval)


def main():
    """Run tracker as standalone script"""
    import sys

    if len(sys.argv) < 6:
        print("Usage: python signal_tracker.py <signals_file> <tracking_file> <telegram_token> <telegram_chat_id> <bot_name> [exchange]")
        sys.exit(1)

    signals_file = sys.argv[1]
    tracking_file = sys.argv[2]
    telegram_token = sys.argv[3]
    telegram_chat_id = sys.argv[4]
    bot_name = sys.argv[5]
    exchange = sys.argv[6] if len(sys.argv) > 6 else 'mexc'

    tracker = SignalTracker(
        signals_file=signals_file,
        tracking_file=tracking_file,
        telegram_token=telegram_token,
        telegram_chat_id=telegram_chat_id,
        exchange_name=exchange,
        bot_name=bot_name
    )

    tracker.monitor_signals(check_interval=300)  # 5 minutes


if __name__ == '__main__':
    main()
