# Complete Usage Guide

## 🚀 Quick Start

```bash
cd ~/tradingview-custom-screener
source venv/bin/activate

# Run built-in strategies
./venv/bin/python run_screener.py              # Quality growth + SBST
./venv/bin/python run_screener.py momentum     # Momentum breakouts
./venv/bin/python run_screener.py sbst-only    # Pure SBST signals
```

## 📊 What You Have Now

### 1. **SuperBuySellTrend Indicator** (Your Pine Script)
   - Converted to Python in `super_buy_sell_trend.py`
   - ATR-based trend following with 2 confirmation levels
   - Detects buy/sell signals automatically

### 2. **Standard Technical Indicators** (`indicators.py`)
   - RSI, MACD, Moving Averages
   - Bollinger Bands, Stochastic, ADX
   - Golden Cross detection

### 3. **Integrated Screener** (`run_screener.py`)
   - Combines ALL indicators
   - Pre-built strategies
   - Easy to customize

## 🎯 Built-in Strategies

### Strategy 1: Quality Growth + SBST
**Best for:** Long-term quality stocks in uptrends

```bash
./venv/bin/python run_screener.py
```

**Filters:**
- RSI: 35-70 (healthy, not overbought)
- ADX > 15 (some trend strength)
- SBST: Confirmed uptrend on both levels

**Use case:** Find quality stocks that your SBST indicator confirms are in uptrends

---

### Strategy 2: Momentum Breakout + Buy Signals
**Best for:** Active trading with strong momentum

```bash
./venv/bin/python run_screener.py momentum
```

**Filters:**
- RSI: 50-75 (strong momentum)
- ADX > 25 (strong trend)
- MACD bullish
- SBST: Recent buy signal

**Use case:** Catch breakouts with SBST buy confirmation

---

### Strategy 3: Pure SBST Signals
**Best for:** Following your indicator exclusively

```bash
./venv/bin/python run_screener.py sbst-only
```

**Filters:**
- SBST: Confirmed uptrend only

**Use case:** Pure trend following based on your SuperBuySellTrend logic

---

### Strategy 4: Custom Filters
**Best for:** Your own criteria

Edit `run_screener.py` or create your own script.

## 🔧 How to Use with TradingView MCP

### Full Workflow:

**Step 1: Get candidates from TradingView (in Warp Agent Mode)**

Ask me:
```
"Screen stocks with ROE > 15%, debt/equity < 0.5, revenue growth > 10%"
```

I'll use the TradingView MCP to get fundamentally strong stocks.

**Step 2: I'll automatically extract the symbols and run your screener**

```python
# This happens automatically when you ask me
symbols = ['AAPL', 'MSFT', ...]  # from TradingView

# Apply your SBST + technical filters
results = screen_with_custom_indicators(symbols, filters)
```

**Step 3: You get combined results**

Stocks that pass BOTH:
- ✅ TradingView fundamental filters (quality)
- ✅ Your SuperBuySellTrend + technical filters

## 📖 Available Filters

### Technical Indicators
```python
filters = {
    'rsi_min': 40,              # RSI lower bound
    'rsi_max': 65,              # RSI upper bound
    'min_adx': 20,              # Minimum trend strength
    'macd_bullish': True,       # MACD histogram > 0
    'require_uptrend': True,    # Price above MA & MA rising
    'require_golden_cross': True,  # SMA50 > SMA200
    'stoch_max': 80,            # Stochastic upper bound
}
```

### SuperBuySellTrend Filters
```python
filters = {
    'sbst_uptrend': True,       # Level 1 uptrend
    'sbst_downtrend': True,     # Level 1 downtrend
    'sbst_confirmed': True,     # Level 1 & Level 2 agree
    'sbst_buy_signal': True,    # Recent buy signal (last 5 days)
}
```

## 💡 Example: Custom Screening

Create your own script:

```python
from screener import screen_with_custom_indicators, print_results

# Your custom stock list
my_watchlist = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'AMD']

# Your custom filters
my_filters = {
    'rsi_min': 45,
    'rsi_max': 60,
    'sbst_uptrend': True,
    'sbst_confirmed': True,
    'sbst_buy_signal': True,  # Must have recent buy signal
}

# Run the screener
results = screen_with_custom_indicators(
    my_watchlist, 
    custom_filters=my_filters,
    include_sbst=True
)

# Display results
print_results(results)
```

## 🔍 Understanding the Output

### Example Output:
```
Symbol   Price      RSI      MACD       ADX      Trend    SBST       SBST Conf  Buy
AAPL     $270.37    54.2     0.123      28.3     UP       UPTREND    UPTREND    🟢
```

**Columns explained:**
- **Symbol**: Ticker
- **Price**: Current close price
- **RSI**: Relative Strength Index (14-period)
- **MACD**: MACD histogram value
- **ADX**: Average Directional Index (trend strength)
- **Trend**: Standard MA-based trend (UP/DOWN)
- **SBST**: SuperBuySellTrend Level 1 trend
- **SBST Conf**: SuperBuySellTrend Level 2 (confirmation)
- **Buy**: 🟢 if recent buy signal

### Signal Meanings:

**SBST Trends:**
- Both UPTREND = Strong confirmed uptrend ✅
- Both DOWNTREND = Strong confirmed downtrend 🔴
- Mismatched = Transitioning, wait for confirmation ⚠️

**Buy Flag (🟢):**
- Appeared within last 5 days
- Level 1 crossed from DOWNTREND to UPTREND

## 🎨 Customization Examples

### Example 1: Conservative Long-term
```python
filters = {
    'rsi_min': 35,
    'rsi_max': 55,              # Not overbought
    'min_adx': 15,              # Gentle trend OK
    'sbst_uptrend': True,
    'sbst_confirmed': True,     # Must be confirmed
}
```

### Example 2: Aggressive Scalping
```python
filters = {
    'rsi_min': 60,              # Already moving
    'rsi_max': 80,
    'min_adx': 30,              # Strong trend
    'macd_bullish': True,
    'sbst_buy_signal': True,    # Fresh signal
}
```

### Example 3: Oversold Recovery
```python
filters = {
    'rsi_min': 25,              # Oversold
    'rsi_max': 40,
    'sbst_uptrend': True,       # But starting to turn
    'macd_bullish': True,
}
```

## 🔗 Integration with Warp Agent Mode

### Method 1: Ask me to screen
```
"Find quality stocks with ROE > 15%, then filter for SBST uptrends"
```

I'll:
1. Use TradingView MCP for fundamentals
2. Extract symbols
3. Run your screener
4. Show combined results

### Method 2: Provide your own list
```
"Screen these stocks with SBST: AAPL, MSFT, GOOGL, NVDA"
```

I'll run your screener on those specific stocks.

### Method 3: Use presets
```
"Run the quality growth SBST strategy"
```

I'll use the predefined strategy from `run_screener.py`.

## 📝 Tips & Best Practices

### 1. **Start Broad, Filter Narrow**
- First: Get 50-100 stocks from TradingView (fundamentals)
- Then: Apply your SBST + technical filters
- Result: 5-15 high-quality candidates

### 2. **Understand Your Filters**
- Too strict = No results (like the test run above)
- Too loose = Too many false positives
- Adjust based on market conditions

### 3. **Combine Confirmation**
```python
# Strong setup = All agree
filters = {
    'require_uptrend': True,    # MA uptrend
    'macd_bullish': True,       # MACD agrees
    'sbst_uptrend': True,       # SBST agrees
    'sbst_confirmed': True,     # Both SBST levels
}
```

### 4. **Monitor Different Timeframes**
Current setup uses daily data. For intraday:
- Modify `period="1d"` in functions
- Use `interval="1h"` or `"5m"`
- Adjust ATR periods accordingly

### 5. **Backtest Your Strategies**
The tool provides current signals. To backtest:
- Use longer `period` parameter
- Look at historical signals in DataFrame
- Track performance over time

## 🚨 Troubleshooting

**No stocks pass filters**
- Filters too strict
- Market conditions don't match criteria
- Try loosening RSI ranges or removing SBST confirmation requirement

**Slow performance**
- Reduce `max_workers` if rate limited
- Screen smaller batches
- Consider caching data

**Missing data for some stocks**
- Stock might be delisted
- Insufficient history (needs 6 months+)
- Check ticker symbol format

## 🎓 Next Steps

### Add More Indicators
Edit `indicators.py` to add your other Pine Script indicators.

### Create More Strategies
Copy strategy functions in `run_screener.py` and customize.

### Automate Alerts
Set up cron jobs to run daily:
```bash
0 16 * * 1-5 cd ~/tradingview-custom-screener && ./venv/bin/python run_screener.py > daily_scan.txt
```

### Export Results
Modify `print_results()` to save CSV:
```python
import pandas as pd
df = pd.DataFrame(results)
df.to_csv('screening_results.csv')
```

## 📞 Quick Reference

```bash
# Activate environment
source ~/tradingview-custom-screener/venv/bin/activate

# Test single stock SBST
python super_buy_sell_trend.py

# Test single stock all indicators  
python indicators.py

# Run strategies
python run_screener.py                # Quality growth
python run_screener.py momentum       # Momentum
python run_screener.py sbst-only      # Pure SBST

# In Warp Agent Mode, just ask:
# "Screen quality stocks with SBST uptrends"
```

---

**Remember:** This screener combines:
1. ✅ TradingView fundamentals (via MCP)
2. ✅ Your SuperBuySellTrend indicator (Pine Script → Python)
3. ✅ Standard technical indicators
4. ✅ Parallel processing for speed

You now have a complete screening pipeline! 🎉
