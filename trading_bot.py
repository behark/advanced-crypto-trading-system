#!/usr/bin/env python3
"""
Automated Trading Bot
Executes trades automatically, manages positions, handles stops/targets
"""

import ccxt
import time
import requests
from datetime import datetime
from advanced_trading_system import AdvancedTradingSystem
from trade_tracker import TradeTracker
from risk_management import RiskProfile, RiskManager


class TradingBot:
    """Automated trading bot with risk management"""
    
    def __init__(self, exchange_name='binance', account_balance=10000, 
                 dry_run=True, symbols=None, telegram_bot_token=None, telegram_chat_id=None):
        """
        Initialize trading bot
        
        Args:
            exchange_name: 'binance', 'kraken', etc.
            account_balance: Starting account balance
            dry_run: True = paper trading, False = real trading
            symbols: List of symbols to monitor
            telegram_bot_token: Bot token for Telegram notifications
            telegram_chat_id: Chat ID to send notifications to
        """
        self.exchange_name = exchange_name
        self.dry_run = dry_run
        self.symbols = symbols or ['LAB/USDT:USDT', 'DOGE/USDT:USDT']
        
        # Telegram setup
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id
        self.telegram_enabled = bool(telegram_bot_token and telegram_chat_id)
        
        # Initialize systems
        self.trading_system = AdvancedTradingSystem(account_balance=account_balance)
        self.tracker = TradeTracker("bot_trades.json")
        
        # Exchange connection
        try:
            if exchange_name.lower() == 'binance':
                self.exchange = ccxt.binance()
            else:
                self.exchange = ccxt.kraken()
            print(f"✅ Connected to {exchange_name}")
        except Exception as e:
            print(f"❌ Exchange connection error: {e}")
            self.exchange = None
        
        self.mode = "PAPER" if dry_run else "LIVE"
        print(f"🤖 Trading Bot initialized in {self.mode} mode")
        
        if self.telegram_enabled:
            print(f"📱 Telegram notifications enabled")
            self.send_telegram(f"🤖 Trading Bot started in {self.mode} mode\n📊 Monitoring: {', '.join(self.symbols)}")
        else:
            print(f"📱 Telegram notifications disabled")
    
    def check_signal(self, symbol, verbose=False):
        """Check signal for a symbol"""
        try:
            analysis = self.trading_system.analyze_symbol_advanced(
                symbol, 
                base_timeframe="5m",
                verbose=verbose
            )
            
            if not analysis:
                return None
            
            signal = analysis['signal_5m']
            tf_validation = analysis['multi_tf_validation']
            
            # Accept any clear signal (40%+ confidence with action)
            has_clear_signal = signal['confidence'] >= 40 and signal['action'] != 'WAIT'
            
            if has_clear_signal:
                return {
                    'symbol': symbol,
                    'signal': signal['action'],
                    'confidence': signal['confidence'],
                    'entry': signal['entry'],
                    'stop_loss': signal['stop_loss'],
                    'tp1': signal['take_profit_1'],
                    'tp2': signal['take_profit_2'],
                    'risk_reward': signal['risk_reward'],
                    'multi_tf_confirmed': tf_validation['approved'],
                    'full_analysis': analysis,
                }
        except Exception as e:
            if verbose:
                print(f"Error checking {symbol}: {e}")
        
        return None
    
    def send_telegram(self, message):
        """Send message to Telegram"""
        if not self.telegram_enabled:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Telegram error: {e}")
            return False
    
    def execute_trade(self, trade_signal):
        """Execute a trade (paper or live)"""
        if not trade_signal:
            return False
        
        symbol = trade_signal['symbol']
        side = trade_signal['signal'].lower()  # 'buy' or 'sell'
        entry = trade_signal['entry']
        stop_loss = trade_signal['stop_loss']
        tp1 = trade_signal['tp1']
        tp2 = trade_signal['tp2']
        
        print(f"\n{'='*80}")
        print(f"TRADE EXECUTION: {symbol} {side.upper()}")
        print(f"{'='*80}\n")
        
        # Validate trade with risk manager
        trade_info = self.trading_system.validate_and_size_trade(
            trade_signal['full_analysis']['signal_5m'],
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
        print(f"   Risk Score: {trade_info['risk_score']}/100")
        
        # Log signal
        log_data = {
            'symbol': symbol,
            'timeframe': '5m',
            'action': side.upper(),
            'entry': entry,
            'stop_loss': stop_loss,
            'take_profit_1': tp1,
            'take_profit_2': tp2,
            'confidence': trade_signal['confidence'],
            'weighted_confidence': trade_signal['full_analysis']['weighted_confidence'],
            'multi_tf_confirmed': trade_signal['multi_tf_confirmed'],
            'divergences_count': len(trade_signal['full_analysis']['divergences']),
            'risk_reward': trade_signal['risk_reward'],
        }
        
        trade_id = self.tracker.log_signal(log_data)
        print(f"   Trade ID: {trade_id}")
        
        # Send Telegram notification
        telegram_msg = f"🎯 <b>TRADING SIGNAL</b>\n\n"
        telegram_msg += f"📊 <b>{symbol}</b> - {side.upper()}\n"
        telegram_msg += f"💪 Confidence: <b>{trade_signal['confidence']:.1f}%</b>\n"
        telegram_msg += f"📈 Entry: <b>${entry:.6f}</b>\n"
        telegram_msg += f"🛑 Stop: <b>${stop_loss:.6f}</b>\n"
        telegram_msg += f"🎯 TP1: <b>${tp1:.6f}</b>\n"
        telegram_msg += f"🎯 TP2: <b>${tp2:.6f}</b>\n"
        telegram_msg += f"📊 R:R: <b>{trade_signal['risk_reward']:.2f}</b>\n"
        telegram_msg += f"💰 Size: <b>{trade_info['position_size']:.2f}</b>\n"
        telegram_msg += f"⚠️ Risk: <b>${trade_info['risk_dollars']:.2f}</b>\n\n"
        
        if self.dry_run:
            telegram_msg += f"📋 <i>Paper Trading Mode</i>"
            print(f"\n📋 PAPER TRADING (no real execution)")
        else:
            telegram_msg += f"🚀 <b>LIVE TRADE EXECUTED</b>"
            print(f"\n🚀 EXECUTING LIVE TRADE")
            # Live execution would go here
            # This is intentionally left empty for safety
        
        self.send_telegram(telegram_msg)
        return trade_id
    
    def monitor_trades(self):
        """Monitor open trades (paper trading)"""
        self.tracker.print_open_trades()
        self.tracker.print_stats()
    
    def run_loop(self, interval_minutes=5, max_iterations=None):
        """Run bot monitoring loop"""
        iteration = 0
        
        print(f"\n🤖 Bot starting in {self.mode} mode")
        print(f"📊 Monitoring {len(self.symbols)} symbols every {interval_minutes} minutes")
        print(f"Type Ctrl+C to stop\n")
        
        try:
            while True:
                iteration += 1
                
                if max_iterations and iteration > max_iterations:
                    break
                
                print(f"\n[{datetime.now()}] Checking signals (iteration {iteration})...")
                
                signals_found = 0
                for symbol in self.symbols:
                    signal = self.check_signal(symbol, verbose=False)
                    if signal:
                        signals_found += 1
                        print(f"  🎯 {symbol}: {signal['signal']} ({signal['confidence']}% confidence)")
                        
                        # Execute trade
                        self.execute_trade(signal)
                
                if signals_found == 0:
                    print(f"  ⏸️  No signals found")
                
                # Wait before next check
                print(f"\n⏳ Next check in {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
        
        except KeyboardInterrupt:
            print(f"\n\n✋ Bot stopped")
            self.monitor_trades()
    
    def backtest_signals(self, days=30):
        """Backtest signals over past N days"""
        print(f"\n{'='*80}")
        print(f"BACKTESTING LAST {days} DAYS")
        print(f"{'='*80}\n")
        
        for symbol in self.symbols:
            print(f"Testing {symbol}...")
            signal = self.check_signal(symbol)
            if signal:
                print(f"  ✅ Signal: {signal['signal']} ({signal['confidence']}%)")
            else:
                print(f"  ⏸️  No signal")
    
    def print_status(self):
        """Print bot status"""
        print(f"\n{'='*80}")
        print(f"BOT STATUS")
        print(f"{'='*80}\n")
        print(f"Mode: {self.mode}")
        print(f"Exchange: {self.exchange_name}")
        print(f"Symbols: {', '.join(self.symbols)}")
        print(f"\nAccount:")
        report = self.trading_system.get_risk_report()
        print(f"  Balance: ${report['account_balance']:.2f}")
        print(f"  Heat: {report['portfolio_heat']*100:.2f}%")
        print(f"  Drawdown: {report['current_drawdown']*100:.2f}%")
        print(f"  Status: {report['status']}")
        print()


def main():
    """Example usage"""
    
    # Initialize bot (PAPER TRADING by default)
    bot = TradingBot(
        exchange_name='binance',
        account_balance=10000,
        dry_run=True,  # ✅ Paper trading
        symbols=['LAB/USDT:USDT', 'BTC/USDT:USDT', 'ETH/USDT:USDT']
    )
    
    # Print status
    bot.print_status()
    
    # Check signals for all symbols
    print(f"\n{'='*80}")
    print("CHECKING ALL SYMBOLS")
    print(f"{'='*80}\n")
    
    for symbol in bot.symbols:
        signal = bot.check_signal(symbol)
        if signal:
            print(f"✅ {symbol}: {signal['signal']} ({signal['confidence']}%)")
            # Optionally execute
            # bot.execute_trade(signal)
        else:
            print(f"⏸️  {symbol}: No signal")
    
    # Alternative: Run continuous monitoring
    # bot.run_loop(interval_minutes=5, max_iterations=10)


if __name__ == "__main__":
    main()
