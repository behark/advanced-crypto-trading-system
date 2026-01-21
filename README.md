# Advanced Crypto Trading System

A comprehensive algorithmic trading system for cryptocurrency markets featuring multi-indicator analysis, multi-timeframe confirmation, advanced risk management, and backtesting capabilities.

## Features

### Trading Strategies
- **Simple Strategy**: SBST + RSI + MACD + ADX (lightweight, fast)
- **Complex Strategy**: Multi-indicator system with 10+ technical indicators
- **Multi-Timeframe Analysis**: 5m, 15m, 1h, and 4h confirmation
- **Smart Money Concepts (SMC)**: Order blocks, FVG, CHoCH detection

### Technical Indicators
- SuperBuySellTrend (SBST) - Primary trend detection
- HalfTrend - Support/resistance levels
- Parabolic SAR - Reversal detection
- Swift Algo - Momentum analysis
- Chandelier Exit - Exit signals
- NRTR (Nick Rypock Trailing Reverse)
- Smart Money Concepts (SMC)
- Traditional indicators: RSI, MACD, ADX, EMAs

### Risk Management
- Kelly Criterion position sizing
- Portfolio heat management (max 6% exposure)
- Drawdown protection (20% max)
- Confidence-based position scaling
- Stop loss and take profit automation

### Analysis Tools
- Real-time market analysis
- Backtesting engine with historical data
- Strategy comparison framework
- Divergence detection
- Weighted confidence scoring
- Multi-channel alerts (Telegram, Discord, Slack)
- Region tagging for signals (e.g., TRADING_COUNTRY=Global)

## Installation

### Prerequisites
```bash
python3 --version  # Requires Python 3.8+
```

### Install Dependencies
```bash
pip install ccxt pandas numpy ta
```

### Required Libraries
- `ccxt`: Exchange connectivity (Binance)
- `pandas`: Data manipulation
- `numpy`: Numerical computations
- `ta`: Technical analysis library

## Quick Start

### 1. Backtest Simple Strategy
```bash
python3 compare_strategies.py backtest-simple -s "LAB/USDT:USDT" -d 180 -t "5m"
```

### 2. Test on Live Data (Simple)
```bash
python3 compare_strategies.py live-simple -s "LAB/USDT:USDT" -t "5m"
```

### 3. Test on Live Data (Complex Multi-Indicator)
```bash
python3 compare_strategies.py live-complex -s "LAB/USDT:USDT" -t "5m"
```

### 4. Compare Both Strategies Side-by-Side
```bash
python3 compare_strategies.py compare -s "LAB/USDT:USDT" -d 180 -t "5m"
```

## Usage Examples

### Single Analysis
```bash
# Analyze LAB/USDT on 5m timeframe
python3 advanced_trading_system.py
```

### Continuous Monitoring
```bash
# Run every 60 seconds
python3 advanced_trading_system.py --continuous

# Run every 5 minutes with custom symbol
python3 advanced_trading_system.py -c -i 300 -s "BTC/USDT:USDT"

# Clear screen between runs for cleaner output
python3 advanced_trading_system.py -c --clear

# Different timeframe
python3 advanced_trading_system.py -c -t "15m"
```

### Command-Line Options
```bash
python3 advanced_trading_system.py --help

Options:
  -c, --continuous        Run continuously instead of once
  -i, --interval SECONDS  Interval between runs (default: 60)
  -s, --symbol SYMBOL     Trading symbol (default: LAB/USDT:USDT)
  -t, --timeframe TF      Base timeframe (default: 5m)
  --clear                 Clear screen between runs
```

## Project Structure

```
tradingview-custom-screener/
├── advanced_trading_system.py   # Main trading system with continuous mode
├── binance_crypto.py            # Market data & signal generation
├── risk_management.py           # Position sizing & risk controls
├── compare_strategies.py        # Strategy comparison & backtesting
├── backtester.py                # Historical backtesting engine
├── indicators.py                # Core technical indicators
├── super_buy_sell_trend.py      # SBST indicator
├── halftrend.py                 # HalfTrend indicator
├── parabolic_sar.py             # Parabolic SAR
├── swift_algo.py                # Swift Algo momentum
├── chandelier_exit.py           # Chandelier Exit
├── nrtr.py                      # NRTR trailing stop
├── smc.py                       # Smart Money Concepts
└── README.md                    # This file
```

## Strategy Comparison

The system includes two trading approaches:

### Simple Strategy (Recommended Starting Point)
- Uses only: SBST + RSI + MACD + ADX
- Faster execution
- Easier to understand and optimize
- Lower false positive rate
- **Start here and validate with backtesting**

### Complex Strategy
- 10+ indicators with weighted scoring
- Multi-timeframe confirmation required
- Divergence detection
- Higher confidence threshold (75%)
- More conservative (fewer trades)

**Recommendation**: Backtest the simple strategy first. Only add complexity if it measurably improves performance.

## Backtesting

### Run Backtest
```bash
python3 backtester.py
```

### Interpret Results
Look for:
- **Win Rate > 50%**: Strategy has edge
- **Avg P&L > 0%**: Profitable over time
- **TP Hits > SL Hits**: Risk/reward working
- **Reasonable trade count**: Not overtrading or undertrading

### Optimize Parameters
Edit parameters in `compare_strategies.py`:
```python
# Conservative (fewer, higher quality trades)
rsi_low=45, rsi_high=65, adx_min=20, require_macd=True

# Aggressive (more trades)
rsi_low=35, rsi_high=75, adx_min=10, require_macd=False
```

## Risk Management

### Default Settings
```python
account_balance = 10000        # Starting capital
max_risk_per_trade = 0.02      # 2% per trade
max_portfolio_heat = 0.06      # 6% total exposure
max_drawdown = 0.20            # 20% max drawdown
confidence_threshold = 75      # Min confidence to trade
```

### Position Sizing Methods
- **Standard**: Fixed 2% risk per trade
- **Kelly Criterion**: Optimal fraction based on edge
- **Confidence-Adjusted**: Scale size with signal quality
- **Portfolio Heat**: Limit based on total exposure

## Supported Exchanges & Symbols

### Binance USD-M Futures
```bash
# Format: BASE/QUOTE:SETTLEMENT
python3 advanced_trading_system.py -s "BTC/USDT:USDT"
python3 advanced_trading_system.py -s "ETH/USDT:USDT"
python3 advanced_trading_system.py -s "LAB/USDT:USDT"
```

### Binance Spot
```bash
# Format: BASE/QUOTE
python3 binance_crypto.py "BTC/USDT" 5m
python3 binance_crypto.py "ETH/USDT" 15m
```

### List Available Symbols
```bash
python3 binance_crypto.py list binance 50
```

## Timeframes

Supported timeframes: `1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `1d`, `1w`, `1M`

## Key Concepts

### Multi-Timeframe Confirmation
Signals on 5m require confirmation from higher timeframes:
- **15m**: Immediate trend alignment
- **1h**: Medium-term trend
- **4h**: Long-term trend direction

At least 2/3 timeframes must align for trade approval.

### Weighted Confidence
Each indicator contributes to overall confidence:
- SBST: 20%
- Swift Algo: 15%
- HalfTrend: 12%
- SMC: 12%
- NRTR: 10%
- PSAR: 10%
- Chandelier: 8%
- RSI: 5%
- MACD: 5%
- ADX: 3%

### Divergence Detection
System detects conflicts between indicators:
- Price/RSI divergence
- SBST/SMC trend disagreement
- Multiple simultaneous reversal signals

## Output Interpretation

### Trade Signal Example
```
5M SIGNAL: BUY (Confidence: 82%)
Weighted Confidence: 85.0%

MULTI-TIMEFRAME VALIDATION:
  Strength: 100%
  Confirmations: 3/3
  Approved: ✅ YES
  Aligned: 15m, 1h, 4h

RISK ASSESSMENT:
  Entry: $0.16720000
  Stop: $0.16580000
  Risk: 0.837%
  R:R: 1:2.50

✅ TRADE APPROVED
Position Size: 1432.50
Risk Dollars: $28.00
Kelly: 5.25%
```

## Performance Monitoring

### Track Results
The system provides:
- Trade-by-trade P&L
- Win rate tracking
- Portfolio heat monitoring
- Drawdown alerts
- Risk score per trade

### Example Output
```
PORTFOLIO RISK REPORT
Balance: $10000.00
Drawdown: 0.00%
Heat: 2.50%
Status: Healthy
```

## Safety Features

- **Graceful Shutdown**: CTRL+C stops safely after current analysis
- **Error Handling**: Continues on API failures
- **Data Validation**: Checks for sufficient candles before analysis
- **Stop Loss Validation**: Ensures SL is logical relative to entry
- **Portfolio Limits**: Prevents over-exposure

## Common Issues

### Insufficient Data
```
❌ Insufficient data for analysis
```
**Solution**: Some symbols have limited history. Use different symbol or shorter lookback.

### High Rejection Rate
```
❌ TRADE REJECTED - Confidence 58% < threshold 75%
```
**Solution**: Lower `confidence_threshold` in risk profile or optimize signal generation.

### No Signals
**Possible causes**:
- Market conditions don't meet criteria
- Timeframe misalignment (5m waiting for 4h confirmation)
- Threshold too high

**Solution**: Run backtests to find optimal parameters for current market.

## Roadmap

- [ ] Database integration for trade tracking
- [ ] Web dashboard for monitoring
- [ ] Paper trading integration
- [ ] Real-time alerts (Telegram/Discord)
- [ ] Machine learning signal optimization
- [ ] Multi-exchange support
- [ ] Automated trade execution

## Disclaimer

**This is a technical analysis tool, not financial advice.**

- Cryptocurrency trading carries significant risk
- Past performance does not guarantee future results
- Always do your own research
- Never risk more than you can afford to lose
- Test thoroughly with paper trading before using real capital
- This software is provided "as is" without warranty

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Include error messages and steps to reproduce

## Acknowledgments

- TradingView for indicator concepts
- CCXT library for exchange connectivity
- Technical analysis community for strategies

---

**Happy Trading! May your backtests be green and your drawdowns shallow.**
