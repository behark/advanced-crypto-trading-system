# Implementation Plan: TradingView Custom Screener & Bot

## Problem Statement
Audit the repository to find concrete issues and broken logic, then propose targeted fixes that improve correctness, safety, and maintainability without changing intended features.

## Current State (What’s Here and How It Works)
- Screening and CLI
  - run_screener.py → orchestrates strategies, calls screener.screen_with_custom_indicators
  - screener.py → merges yfinance-based indicators (indicators.py) with SBST (super_buy_sell_trend.py); filtering and printing
- Indicators and Signals (yfinance data)
  - indicators.py → RSI/MACD/SMAs/BB/ATR/Stochastic/ADX/OBV helpers + latest signal snapshot
  - super_buy_sell_trend.py → SBST levels, trend/trendx, buy/sell/confirm, atr
  - halftrend.py, parabolic_sar.py, chandelier_exit.py, nrtr.py, swift_algo.py, smc.py → auxiliary signals/structure
- Binance Crypto Flow (ccxt data)
  - binance_crypto.py → fetch_ohlcv from ccxt; compute SBST + aux indicators; composite analysis; trade signal generation; multi-TF validation
- Trading System & Bot
  - advanced_trading_system.py → wraps binance_crypto for analysis, validation, sizing (risk_management)
  - risk_management.py → RiskProfile, RiskManager (sizing/validation/reporting); SignalOptimizer (not used by AdvancedTradingSystem)
  - trading_bot.py → bot loop, Telegram notify, execution skeleton, TradeTracker logging
  - trade_tracker.py → JSON log + stats/CSV export
- Backtesting
  - backtester.py → intended historical test of signals

## Confirmed Issues (with evidence)
1) backtester.py misuses analyze_crypto_binance and will error
   - Calls analyze_crypto_binance expecting a DataFrame and passes an unsupported argument:
     ```python
     # backtester.py
     df = analyze_crypto_binance(self.symbol, timeframe='1d', limit=self.lookback_days)
     if not df:
         print("❌ Insufficient data")
     ```
     But the actual signature is:
     ```python
     # binance_crypto.py
     def analyze_crypto_binance(symbol, timeframe="5m", periods=10, multiplier1=0.8, multiplier2=1.6):
     ```
   - Later treats df as a DataFrame and loops by index, then re-calls analyze_crypto_binance inside the loop:
     ```python
     for i in range(len(df) - 5):
         analysis = analyze_crypto_binance(self.symbol, timeframe='1d')
         if analysis:
             signal = {
                 'date': df.index[i],
                 'price': df.iloc[i]['Close'],
                 'trend': df.iloc[i].get('trend', 'unknown'),
             }
     ```
   - Root cause: analyze_crypto_binance returns a dict (single snapshot), not a historical DataFrame. The function also doesn’t accept a `limit` parameter.

2) start_bot.py contains hard-coded secrets (security risk)
   ```python
   TELEGRAM_BOT_TOKEN = "7836159863:AAHkoO9BGPi3LfHut09wxesgNKQdrTliAKY"
   TELEGRAM_CHAT_ID = 1507876704
   ```
   - Credentials should not be committed; bot should read from env variables.

3) Minor clarity/safety items
   - nrtr.py sell signal precedence is correct but hard to read; parentheses would improve clarity:
     ```python
     if (trend[i] == -1 and trend[i-1] == 0) or (trend[i] == -1 and trend[i-1] == 1):
     ```
   - trade_tracker.py formatting assumes numeric values for open trades; if any field were None, printing would error (current call sites provide values, but adding guards is safer).
   - Repository hygiene: large files named `pd`, `ta`, `yf` in repo root are unrelated PostScript documents; they don’t affect current imports but are easy to confuse with common Python aliases/modules.

## Proposed Changes (Do Not Execute Yet)
1) Backtester: rebuild to operate on historical OHLCV and replay signals
   - Replace the misuse of analyze_crypto_binance with true historical data via ccxt helper:
     - Use binance_crypto.get_binance_data(symbol, timeframe='1d', limit=lookback_days) to fetch candles.
   - For each bar (e.g., rolling window), compute minimal indicators needed for a deterministic signal and collect outcomes:
     - Option A (faster): use calculate_super_buy_sell_trend + indicators.calculate_rsi/macd/adx and then a lightweight rule-set (binance_crypto.generate_trade_signal_simple).
     - Option B (heavier): reuse the full pipeline by incrementally applying the computations per bar (slower, more accurate to live path).
   - Record signals, hypothetical entries/exits using SBST levels/ATR-based stops, and compute aggregate stats (win rate, avg P&L, R:R).
   - Remove unsupported `limit` arg; ensure function variables and return types are consistent (DataFrame for history, dicts for snapshots).

2) Secrets handling
   - Remove hard-coded Telegram credentials from start_bot.py; load via environment variables (e.g., TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID) and fail fast if missing.
   - Optionally support a `.env` loader (only if desired) and update README with setup steps.

3) Minor improvements (safe, scoped)
   - nrtr.py: add parentheses in sell condition for readability (no behavior change).
   - trade_tracker.py: add defensive formatting for open trades (handle None gracefully).
   - Repo hygiene: move/remove `pd`, `ta`, `yf` artifacts to avoid confusion.

## Validation Plan
- Unit/behavior checks
  - Backtester: deterministic run on a small lookback (e.g., 120 daily candles) should complete without exceptions and output non-empty summary for liquid symbols (e.g., BTC/USDT, ETH/USDT).
  - Consistency: compare a handful of backtest signals with live snapshot logic on the same dates to confirm alignment within expected tolerance.
- Smoke tests
  - run_screener.py strategies execute and print results without errors.
  - trading_bot.py main path (dry_run) initializes, prints status, checks several symbols, and logs signals to TradeTracker.
- Security
  - start_bot.py requires env vars and refuses to start if missing; confirm no secrets in repo.

## Execution Order
1) Rebuild backtester (functional correctness, unblock validation)
2) Secrets management change in start_bot.py
3) Minor clarity/safety edits (nrtr.py, trade_tracker.py) and repo hygiene

## Acceptance Criteria
- Backtester completes without errors and produces plausible metrics.
- No hard-coded secrets remain; bot runs with env-based credentials.
- No regressions in run_screener.py, trading_bot.py (dry-run), or indicator modules.
