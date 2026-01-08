# 🚀 Trading System Commands

## Quick Signal Scanning

### Scan for 75%+ signals (default)
```bash
python3 scan_signals.py
```

### Scan for 80%+ signals (higher threshold)
```bash
python3 scan_signals.py 80
```

### Scan for 90%+ signals (rare gems like your LAB trade)
```bash
python3 scan_signals.py 90
```

---

## Check Specific Pair

### Check LAB/USDT
```bash
python3 -c "from advanced_trading_system import AdvancedTradingSystem; sys = AdvancedTradingSystem(); analysis = sys.analyze_symbol_advanced('LAB/USDT:USDT', verbose=True)"
```

### Check DOGE/USDT
```bash
python3 -c "from advanced_trading_system import AdvancedTradingSystem; sys = AdvancedTradingSystem(); analysis = sys.analyze_symbol_advanced('DOGE/USDT:USDT', verbose=True)"
```

### Check any pair (replace SYMBOL)
```bash
python3 -c "from advanced_trading_system import AdvancedTradingSystem; sys = AdvancedTradingSystem(); analysis = sys.analyze_symbol_advanced('SYMBOL/USDT:USDT', verbose=True)"
```

Examples:
- `BTC/USDT:USDT`
- `ETH/USDT:USDT`
- `PEPE/USDT:USDT`
- `SOL/USDT:USDT`

---

## Bot Commands

### Start bot (1-minute checks, Telegram enabled)
```bash
python3 start_bot.py
```

### Check bot status
```bash
python3 -c "from trade_tracker import TradeTracker; TradeTracker('bot_trades.json').print_stats()"
```

### View trade history
```bash
cat bot_trades.json
```

---

## Manual Trading Commands

### Log a trade manually
```python
from trade_tracker import TradeTracker

tracker = TradeTracker()
tracker.log_signal({
    'symbol': 'LAB/USDT:USDT',
    'action': 'BUY',
    'entry': 0.15,
    'stop_loss': 0.14,
    'take_profit_1': 0.17,
    'confidence': 90
})
```

### Close a trade
```python
tracker.close_trade('trade_id_here', exit_price=0.17, outcome='WIN')
```

### View statistics
```python
tracker.print_stats()
```

---

## Backtesting

### Run backtest
```bash
python3 backtester.py
```

---

## Edit Scanner Pairs

Edit `scan_signals.py` and modify the `PAIRS` list:

```python
PAIRS = [
    'LAB/USDT:USDT',
    'DOGE/USDT:USDT',
    # Add more pairs here
    'YOUR/PAIR:USDT'
]
```

---

## Quick Examples

### Find 75%+ signals across 10 pairs
```bash
python3 scan_signals.py
```

### Find super high confidence (90%+)
```bash
python3 scan_signals.py 90
```

### Check LAB status
```bash
python3 -c "from advanced_trading_system import AdvancedTradingSystem; import warnings; warnings.filterwarnings('ignore'); sys = AdvancedTradingSystem(); a = sys.analyze_symbol_advanced('LAB/USDT:USDT'); print(f\"LAB: {a['signal_5m']['action']} - {a['signal_5m']['confidence']:.1f}%\")"
```

### One-liner for multiple pairs
```bash
for pair in LAB DOGE BTC ETH; do python3 -c "from advanced_trading_system import AdvancedTradingSystem; import warnings; warnings.filterwarnings('ignore'); sys = AdvancedTradingSystem(); a = sys.analyze_symbol_advanced('${pair}/USDT:USDT'); print(f'${pair}: {a[\"signal_5m\"][\"action\"]} - {a[\"signal_5m\"][\"confidence\"]:.1f}%')" 2>/dev/null; done
```

---

## Useful Aliases (add to ~/.zshrc)

```bash
# Quick scan
alias scan='cd ~/tradingview-custom-screener && python3 scan_signals.py'

# Check LAB
alias lab='cd ~/tradingview-custom-screener && python3 -c "from advanced_trading_system import AdvancedTradingSystem; import warnings; warnings.filterwarnings(\"ignore\"); sys = AdvancedTradingSystem(); a = sys.analyze_symbol_advanced(\"LAB/USDT:USDT\"); print(f\"LAB: {a[\"signal_5m\"][\"action\"]} - {a[\"signal_5m\"][\"confidence\"]:.1f}%\")"'

# Start bot
alias bot='cd ~/tradingview-custom-screener && python3 start_bot.py'
```

After adding, run:
```bash
source ~/.zshrc
```

Then you can just type:
- `scan` - Run signal scanner
- `lab` - Check LAB status
- `bot` - Start trading bot

---

## Summary

**Most used commands:**

1. **Scan all pairs:** `python3 scan_signals.py`
2. **Check LAB:** See "Check LAB status" above
3. **Start bot:** `python3 start_bot.py`

That's it! Keep it simple. 🚀
