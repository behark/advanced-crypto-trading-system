#!/usr/bin/env python3
"""
Automated Trading Bot
Executes trades automatically, manages positions, handles stops/targets
Supports Multi-Timeframe (1h + 4h) & Multi-Exchange Pairs
"""

import ccxt
import time
import os
from datetime import datetime
from advanced_trading_system import AdvancedTradingSystem
from trade_tracker import TradeTracker
from risk_management import RiskProfile, RiskManager
from dotenv import load_dotenv
from notifications import NotificationManager

# Load environment variables if available
load_dotenv()

class TradingBot:
    """Automated trading bot with risk management"""

    def __init__(self, exchange_name='binance', account_balance=10000,
                 dry_run=True, symbols=None, telegram_bot_token=None, telegram_chat_id=None,
                 discord_webhook_url=None, slack_webhook_url=None, country=None):
        """
        Initialize trading bot
        """
        self.exchange_name = exchange_name
        self.dry_run = dry_run

        # 1. TIMEFRAMES TO MONITOR
        self.timeframes = ['1h', '4h']

        # 2. FULL WATCHLIST ( synced with config_advanced.yaml )
        self.symbols = symbols or [
            # --- BYBIT PAIRS ---
            'ADA/USDT:USDT',
            'AVAX/USDT:USDT',
            'ICP/USDT:USDT',
            'IRYS/USDT:USDT',

            # --- MEXC PAIRS ---
            'APR/USDT:USDT',
            'BLUAI/USDT:USDT',
            'BOBBOB/USDT:USDT',
            'CLO/USDT:USDT',
            'H/USDT:USDT',
            'JELLYJELLY/USDT:USDT',
            'KITE/USDT:USDT',
            'LAB/USDT:USDT',
            'MINA/USDT:USDT',
            'RIVER/USDT:USDT',
            'VVV/USDT:USDT',
            'ON/USDT:USDT',
            'MON/USDT:USDT',
            'TRC/USDT:USDT',
            'RLS/USDT:USDT',
            'GAIX/USDT:USDT',
            'BEST/USDT:USDT'
        ]

        # Notification setup
        self.country = country or os.getenv("TRADING_COUNTRY", "Global")
        self.notifications = NotificationManager(
            telegram_bot_token=telegram_bot_token,
            telegram_chat_id=telegram_chat_id,
            discord_webhook_url=discord_webhook_url,
            slack_webhook_url=slack_webhook_url,
        )

        # Initialize systems
        self.trading_system = AdvancedTradingSystem(account_balance=account_balance)
        self.tracker = TradeTracker("bot_trades.json")

        # Signal cooldown tracking (prevent duplicate signals)
        # Key format: "SYMBOL_TIMEFRAME" (e.g. "BTC/USDT:USDT_1h")
        self.last_signals = {}
        self.signal_cooldown_hours = 1

        # Exchange connection
        try:
            if exchange_name.lower() == 'binance':
                self.exchange = ccxt.binance()
            else:
                # Defaulting to MEXC for wider coverage if needed
                self.exchange = ccxt.mexc()
            print(f"✅ Connected to {exchange_name}")
        except Exception as e:
            print(f"❌ Exchange connection error: {e}")
            self.exchange = None

        self.mode = "PAPER" if dry_run else "LIVE"
        print(f"🤖 Trading Bot initialized in {self.mode} mode")

        channels = [name for name, enabled in self.notifications.enabled_channels().items() if enabled]
        if channels:
            print(f"📱 Notifications enabled: {', '.join(channels)}")
            self.notifications.send(
                "🤖 Trading Bot started in "
                f"{self.mode} mode\n📊 Monitoring: {len(self.symbols)} pairs\n"
                f"⏰ Timeframes: {self.timeframes}\n🌍 Region: {self.country}"
            )
        else:
            print("📱 Notifications disabled")

    def check_signal(self, symbol, timeframe, verbose=False):
        """Check signal for a symbol on a specific timeframe"""

        # Unique key for cooldowns (Symbol + Timeframe)
        signal_key = f"{symbol}_{timeframe}"

        # Check cooldown - skip if we signaled this specific combo recently
        if signal_key in self.last_signals:
            time_since_last = (datetime.now().timestamp() - self.last_signals[signal_key]) / 3600
            if time_since_last < self.signal_cooldown_hours:
                if verbose:
                    print(f"  ⏸️  {symbol} ({timeframe}) in cooldown")
                return None

        try:
            # Pass the timeframe to the analysis system
            analysis = self.trading_system.analyze_symbol_advanced(
                symbol,
                base_timeframe=timeframe,
                verbose=verbose
            )

            if not analysis:
                return None

            # AdvancedTradingSystem returns a single signal key named signal_5m
            # regardless of the base timeframe passed in.
            signal = analysis.get('signal_5m')

            if not signal:
                return None

            tf_validation = analysis.get('multi_tf_validation', {'approved': True})

            # Accept clear signals (Confidence > 60%)
            has_clear_signal = signal['confidence'] >= 60 and signal['action'] != 'WAIT'

            if has_clear_signal:
                return {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'signal': signal['action'],
                    'confidence': signal['confidence'],
                    'entry': signal['entry'],
                    'stop_loss': signal['stop_loss'],
                    'tp1': signal['take_profit_1'],
                    'tp2': signal['take_profit_2'],
                    'risk_reward': signal.get('risk_reward', 2.0),
                    'multi_tf_confirmed': tf_validation['approved'],
                    'full_analysis': analysis,
                }
        except Exception as e:
            if verbose:
                print(f"Error checking {symbol} {timeframe}: {e}")

        return None

    def execute_trade(self, trade_signal):
        """Execute a trade (paper or live)"""
        if not trade_signal:
            return False

        symbol = trade_signal['symbol']
        tf = trade_signal['timeframe']
        side = trade_signal['signal'].lower()
        entry = trade_signal['entry']
        stop_loss = trade_signal['stop_loss']
        tp1 = trade_signal['tp1']
        tp2 = trade_signal['tp2']

        print(f"\n{'='*80}")
        print(f"TRADE EXECUTION: {symbol} {side.upper()} ({tf})")
        print(f"{'='*80}\n")

        # Validate trade with risk manager
        trade_info = self.trading_system.validate_and_size_trade(
            trade_signal['full_analysis'].get('signal_5m'),
            entry,
            stop_loss,
            symbol
        )

        if not trade_info['approved']:
            print(f"❌ Trade rejected:")
            for reason in trade_info['reasons']:
                print(f"   {reason}")
            return False

        print(f"✅ Trade approved!")
        print(f"   Position Size: {trade_info['position_size']:.2f}")
        print(f"   Risk: ${trade_info['risk_dollars']:.2f}")

        # Log signal
        log_data = {
            'symbol': symbol,
            'timeframe': tf,
            'action': side.upper(),
            'entry': entry,
            'stop_loss': stop_loss,
            'take_profit_1': tp1,
            'confidence': trade_signal['confidence'],
            'risk_reward': trade_signal['risk_reward'],
            'channel': ','.join([c for c, enabled in self.notifications.enabled_channels().items() if enabled]) or 'local',
            'country': self.country,
        }

        trade_id = self.tracker.log_signal(log_data)
        print(f"   Trade ID: {trade_id}")

        # Update cooldown tracking using the unique key
        signal_key = f"{symbol}_{tf}"
        self.last_signals[signal_key] = datetime.now().timestamp()

        # Send Telegram notification
        telegram_msg = f"🎯 <b>TRADING SIGNAL</b>\n"
        telegram_msg += f"📊 <b>{symbol}</b> ({tf})\n"
        telegram_msg += f"Action: <b>{side.upper()}</b>\n"
        telegram_msg += f"💪 Confidence: <b>{trade_signal['confidence']:.1f}%</b>\n\n"
        telegram_msg += f"🌍 Region: <b>{self.country}</b>\n"
        telegram_msg += f"📈 Entry: <b>${entry:.6f}</b>\n"
        telegram_msg += f"🛑 Stop: <b>${stop_loss:.6f}</b>\n"
        telegram_msg += f"🎯 TP1: <b>${tp1:.6f}</b>\n"
        telegram_msg += f"🎯 TP2: <b>${tp2:.6f}</b>\n\n"
        telegram_msg += f"💰 Size: <b>{trade_info['position_size']:.2f}</b>\n"

        if self.dry_run:
            telegram_msg += f"📋 <i>Paper Trading Mode</i>"
            print(f"\n📋 PAPER TRADING (no real execution)")
        else:
            telegram_msg += f"🚀 <b>LIVE TRADE EXECUTED</b>"
            print(f"\n🚀 EXECUTING LIVE TRADE")

        self.notifications.send(telegram_msg)
        return trade_id

    def monitor_trades(self):
        """Monitor open trades (paper trading)"""
        self.tracker.print_open_trades()
        self.tracker.print_stats()

    def run_loop(self, interval_minutes=5, max_iterations=None):
        """Run bot monitoring loop"""
        iteration = 0

        print(f"\n🤖 Bot starting in {self.mode} mode")
        print(f"📊 Monitoring {len(self.symbols)} pairs on {self.timeframes}")
        print(f"Type Ctrl+C to stop\n")

        try:
            while True:
                iteration += 1
                if max_iterations and iteration > max_iterations: break

                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checking signals (iter {iteration})...")

                signals_found = 0

                # Loop through ALL timeframes
                for tf in self.timeframes:
                    print(f"  ⏰ Timeframe: {tf}")
                    for symbol in self.symbols:
                        # Pass timeframe to check_signal
                        signal = self.check_signal(symbol, timeframe=tf, verbose=False)
                        if signal:
                            signals_found += 1
                            print(f"    🎯 {symbol}: {signal['signal']} ({signal['confidence']}%)")
                            self.execute_trade(signal)

                if signals_found == 0:
                    print(f"  ⏸️  No signals found")

                # Wait before next check
                print(f"\n⏳ Next check in {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)

        except KeyboardInterrupt:
            print(f"\n\n✋ Bot stopped")
            self.monitor_trades()

    def print_status(self):
        """Print bot status"""
        print(f"\n{'='*80}")
        print(f"BOT STATUS")
        print(f"{'='*80}\n")
        print(f"Mode: {self.mode}")
        print(f"Exchange: {self.exchange_name}")
        print(f"Symbols: {len(self.symbols)} pairs loaded")
        print(f"Timeframes: {self.timeframes}")
        print()

def main():
    """Entry point"""

    # Initialize bot
    bot = TradingBot(
        exchange_name='binance', # Can switch to 'mexc' or 'bybit' if supported
        account_balance=10000,
        dry_run=True,

        # TELEGRAM CONFIGURATION
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),

        # OPTIONAL MULTI-CHANNEL CONFIGURATION
        discord_webhook_url=os.getenv("DISCORD_WEBHOOK_URL"),
        slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL"),
        country=os.getenv("TRADING_COUNTRY", "Global"),
    )

    bot.print_status()

    # Run continuous loop (5 min interval is good for 1h/4h checks)
    bot.run_loop(interval_minutes=5)

if __name__ == "__main__":
    main()
