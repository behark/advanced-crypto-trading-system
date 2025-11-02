# 🤖 Trading Bot Tools - Complete Guide

## Tools Overview

You now have 3 powerful tools:

1. **Trade Tracker** (`trade_tracker.py`) - Log signals & calculate stats
2. **Backtester** (`backtester.py`) - Test system on historical data
3. **Trading Bot** (`trading_bot.py`) - Automated trading with risk management

---

## 🎯 Tool #1: Trade Tracker

**Purpose:** Track all signals and calculate real trading statistics

### Quick Usage
```python
from trade_tracker import TradeTracker

tracker = TradeTracker()

# Log a signal
signal_data = {
    'symbol': 'LAB/USDT',
    'action': 'SELL',
    'entry': 0.16209,
    'stop_loss': 0.16493,
    'take_profit_1': 0.15795,
    'take_profit_2': 0.15382,
    'confidence': 95,
    'weighted_confidence': 78.5,
    'multi_tf_confirmed': True,
    'divergences_count': 1,
    'risk_reward': 1.46,
}

trade_id = tracker.log_signal(signal_data)
print(f"Trade #{trade_id} logged")

# Close a trade when you exit
tracker.close_trade(trade_id, exit_price=0.15500, exit_reason="TP1_HIT")

# View stats
tracker.print_stats()
tracker.print_open_trades()

# Export to CSV
tracker.export_csv("my_trades.csv")
```

### What it Tracks
- Entry/exit prices
- Confidence levels
- P&L and win rate
- Best/worst trades
- Total statistics

---

## 📊 Tool #2: Backtester

**Purpose:** Validate system on historical data

### Quick Usage
```python
from backtester import Backtester

backtest = Backtester('LAB/USDT:USDT', lookback_days=180)
results = backtest.backtest()

print(results)
```

### Outputs
- Historical signal accuracy
- Win rate estimate
- Ready-for-trading confirmation

---

## 🤖 Tool #3: Trading Bot

**Purpose:** Fully automated trading with all safety features

### Quick Usage (Paper Trading - Safe!)
```python
from trading_bot import TradingBot

# Initialize BOT (PAPER TRADING by default)
bot = TradingBot(
    exchange_name='binance',
    account_balance=10000,
    dry_run=True,  # ✅ Paper trading (no real money)
    symbols=['LAB/USDT:USDT', 'BTC/USDT:USDT', 'ETH/USDT:USDT']
)

# Check all signals
for symbol in bot.symbols:
    signal = bot.check_signal(symbol)
    if signal:
        print(f"✅ {symbol}: {signal['signal']}")

# Optional: Run continuous monitoring
# bot.run_loop(interval_minutes=5, max_iterations=10)
```

### Bot Features
- ✅ Multi-symbol monitoring
- ✅ Risk validation before execution
- ✅ Automatic position sizing (Kelly Criterion)
- ✅ Paper trading (default - SAFE!)
- ✅ Trade logging
- ✅ Live statistics

---

## 🚀 Usage Workflow

### Week 1: Paper Trading (Track Results)
```bash
# Day 1: Manually trade + log with tracker
python -c "
from trade_tracker import TradeTracker
tracker = TradeTracker()
# Log each trade manually
"

# View stats daily
python -c "
from trade_tracker import TradeTracker
tracker = TradeTracker()
tracker.print_stats()
"
```

### Week 2: Run Bot (Monitor Only)
```bash
# Check signals automatically
python trading_bot.py
```

### Week 3: Backtest Results
```bash
# Validate on historical data
python backtester.py
```

### Week 4+: Live Trading (Optional)
```bash
# Only after validation!
# Change: dry_run=False
```

---

## 📈 Example: Full Workflow

```python
from advanced_trading_system import AdvancedTradingSystem
from trade_tracker import TradeTracker
from trading_bot import TradingBot

# 1. ANALYZE
system = AdvancedTradingSystem()
analysis = system.analyze_symbol_advanced('LAB/USDT:USDT')

# 2. LOG SIGNAL
tracker = TradeTracker()
signal = analysis['signal_5m']
log_data = {
    'symbol': 'LAB/USDT',
    'action': signal['action'],
    'entry': signal['entry'],
    'stop_loss': signal['stop_loss'],
    'take_profit_1': signal['take_profit_1'],
    'take_profit_2': signal['take_profit_2'],
    'confidence': signal['confidence'],
    'weighted_confidence': analysis['weighted_confidence'],
    'multi_tf_confirmed': analysis['multi_tf_validation']['approved'],
    'divergences_count': len(analysis['divergences']),
    'risk_reward': signal['risk_reward'],
}
trade_id = tracker.log_signal(log_data)

# 3. EXECUTE (Paper trading)
bot = TradingBot(dry_run=True)
bot.execute_trade(signal)

# 4. CLOSE & TRACK
# Later when you exit...
tracker.close_trade(trade_id, exit_price=0.155)
tracker.print_stats()
```

---

## 🎯 Commands Cheat Sheet

```bash
# 1. Quick signal check
python trading_bot.py

# 2. View trade statistics
python -c "
from trade_tracker import TradeTracker
TradeTracker().print_stats()
"

# 3. See open trades
python -c "
from trade_tracker import TradeTracker
TradeTracker().print_open_trades()
"

# 4. Backtest system
python backtester.py

# 5. Run bot (once per day)
python trading_bot.py

# 6. Export trades to CSV
python -c "
from trade_tracker import TradeTracker
TradeTracker().export_csv('trades.csv')
"
```

---

## ⚠️ Safety Features (All Enabled)

✅ **Paper trading by default** - No real money risked
✅ **Risk validation** - Each trade scored 0-100
✅ **Position sizing** - Kelly Criterion math
✅ **Portfolio heat** - Max 6% exposure
✅ **Drawdown protection** - Stop at 20% loss
✅ **Multi-TF confirmation** - 2/3 timeframes required
✅ **Confidence threshold** - Min 75% required
✅ **Trade logging** - Every signal tracked

---

## 📋 Next Steps

1. **Today:** Run `python trading_bot.py` to check signals
2. **This week:** Use `TradeTracker` to log all manual trades
3. **Next week:** Run backtester to validate
4. **Week 4:** Switch to `dry_run=False` for live (optional)

---

## 💡 Pro Tips

- **Always start with `dry_run=True`** (paper trading)
- **Log every single signal** - builds valuable data
- **Check stats weekly** - track win rate
- **Run bot daily** - consistent signal generation
- **Backtest before going live** - validate system

---

**Status: ALL TOOLS READY** ✅

Ready to start? Run: `python trading_bot.py`
