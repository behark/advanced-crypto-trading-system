#!/usr/bin/env python3
"""
Backtester - Historical replay using ccxt data and SBST + lightweight signal rules
- Fetches OHLCV via binance_crypto.get_binance_data
- Computes indicators once, then evaluates signals per bar
- Simulates TP1/SL outcomes with a bounded lookahead window
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import pandas as pd

from binance_crypto import (
    get_binance_data,
    generate_trade_signal_simple,
)
from super_buy_sell_trend import calculate_super_buy_sell_trend
from indicators import (
    calculate_rsi,
    calculate_macd,
    calculate_moving_averages,
    calculate_adx,
)


@dataclass
class TradeResult:
    index: int
    date: pd.Timestamp
    action: str
    entry: float
    stop: float
    tp1: float
    exit: float
    exit_reason: str
    pnl: float
    pnl_pct: float


class Backtester:
    """Backtest trading signals on historical data"""

    def __init__(
        self,
        symbol: str,
        lookback_days: int = 180,
        timeframe: str = "1d",
        rsi_low: float = 40,
        rsi_high: float = 70,
        adx_min: float = 15,
        require_macd: bool = True,
    ):
        self.symbol = symbol
        self.lookback_days = lookback_days
        self.timeframe = timeframe
        self.trades: List[TradeResult] = []
        self.summary: Dict = {}
        self.rule_params = {
            'rsi_low': rsi_low,
            'rsi_high': rsi_high,
            'adx_min': adx_min,
            'require_macd': require_macd,
        }

    def _prepare_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        # Core set used by generate_trade_signal_simple
        df = calculate_super_buy_sell_trend(df, periods=10, multiplier1=0.8, multiplier2=1.6)
        df = calculate_rsi(df)
        df = calculate_macd(df)
        df = calculate_moving_averages(df, periods=[10, 20, 50])
        df = calculate_adx(df)
        return df

    def _first_valid_index(self, df: pd.DataFrame) -> int:
        # Ensure required columns are populated
        req = [
            "RSI",
            "MACDh_12_26_9",
            "ADX_14",
            "atr",  # from SBST
            "up_level",
            "dn_level",
            "trend",
            "trendx",
        ]
        valid = df[req].notna().all(axis=1)
        if not valid.any():
            return len(df)
        # Get the first label where all requirements are non-NaN
        first_label = valid.idxmax()
        # Convert label to positional index
        try:
            loc = df.index.get_loc(first_label)
            if isinstance(loc, slice):
                return loc.start or 0
            return int(loc)
        except Exception:
            # Fallback to last warm index
            return max(0, len(df) - 1)

    def _build_analysis_at(self, df: pd.DataFrame, i: int) -> Optional[Dict]:
        if i <= 5:
            return None
        latest = df.iloc[i]
        # Recent windows within computed history up to i
        window_start = max(0, i - 4)
        recent_buy = df['buy_signal'].iloc[window_start:i + 1].any()
        recent_sell = df['sell_signal'].iloc[window_start:i + 1].any()
        recent_buy_confirm = df['buy_confirm'].iloc[window_start:i + 1].any()
        recent_sell_confirm = df['sell_confirm'].iloc[window_start:i + 1].any()

        trend = 'UPTREND' if latest['trend'] == 1 else 'DOWNTREND'
        trend_confirmed = 'UPTREND' if latest['trendx'] == 1 else 'DOWNTREND'
        trend_aligned = trend == trend_confirmed

        analysis = {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'timestamp': latest.name,
            'price': float(latest['Close']),
            'price_change_5c': float(((latest['Close'] - df['Close'].iloc[max(0, i - 5)]) / df['Close'].iloc[max(0, i - 5)]) * 100),

            'trend': trend,
            'trend_confirmed': trend_confirmed,
            'trend_aligned': trend_aligned,
            'current_buy_signal': bool(latest['buy_signal']),
            'current_sell_signal': bool(latest['sell_signal']),
            'current_buy_confirm': bool(latest['buy_confirm']),
            'current_sell_confirm': bool(latest['sell_confirm']),
            'recent_buy': bool(recent_buy),
            'recent_sell': bool(recent_sell),
            'recent_buy_confirm': bool(recent_buy_confirm),
            'recent_sell_confirm': bool(recent_sell_confirm),

            'up_level': float(latest['up_level']),
            'dn_level': float(latest['dn_level']),
            'upx_level': float(latest['upx_level']),
            'dnx_level': float(latest['dnx_level']),

            'rsi': float(latest.get('RSI')) if pd.notna(latest.get('RSI')) else None,
            'macd': float(latest.get('MACD_12_26_9')) if pd.notna(latest.get('MACD_12_26_9')) else None,
            'macd_signal': float(latest.get('MACDs_12_26_9')) if pd.notna(latest.get('MACDs_12_26_9')) else None,
            'macd_hist': float(latest.get('MACDh_12_26_9')) if pd.notna(latest.get('MACDh_12_26_9')) else None,
            'adx': float(latest.get('ADX_14')) if pd.notna(latest.get('ADX_14')) else None,
            'ema_10': float(latest.get('EMA_10')) if pd.notna(latest.get('EMA_10')) else None,
            'ema_20': float(latest.get('EMA_20')) if pd.notna(latest.get('EMA_20')) else None,
            'sma_50': float(latest.get('SMA_50')) if pd.notna(latest.get('SMA_50')) else None,
            'atr': float(latest['atr']) if pd.notna(latest.get('atr')) else 0.0,
        }
        return analysis

    def _simulate_trade(self, df: pd.DataFrame, i: int, signal: Dict, lookahead: int = 20) -> Optional[TradeResult]:
        action = signal['action']
        if action not in ['BUY', 'SELL']:
            return None

        entry = float(signal['entry'])
        stop = float(signal['stop_loss'])
        tp1 = float(signal['take_profit_1'])

        end = min(len(df) - 1, i + lookahead)
        exit_price = entry
        exit_reason = 'TIME'

        for j in range(i + 1, end + 1):
            high = float(df['High'].iloc[j])
            low = float(df['Low'].iloc[j])
            if action == 'BUY':
                # SL first, then TP to be conservative
                if low <= stop:
                    exit_price = stop
                    exit_reason = 'SL'
                    break
                if high >= tp1:
                    exit_price = tp1
                    exit_reason = 'TP1'
                    break
            else:  # SELL
                if high >= stop:
                    exit_price = stop
                    exit_reason = 'SL'
                    break
                if low <= tp1:
                    exit_price = tp1
                    exit_reason = 'TP1'
                    break
        else:
            # No hit within window; exit at last close
            exit_price = float(df['Close'].iloc[end])
            exit_reason = 'TIME'

        pnl = (exit_price - entry) if action == 'BUY' else (entry - exit_price)
        pnl_pct = (pnl / entry) * 100 if entry != 0 else 0.0

        return TradeResult(
            index=i,
            date=df.index[i],
            action=action,
            entry=entry,
            stop=stop,
            tp1=tp1,
            exit=exit_price,
            exit_reason=exit_reason,
            pnl=pnl,
            pnl_pct=pnl_pct,
        )

    def backtest(self) -> Optional[Dict]:
        print(f"\n{'='*80}")
        print(f"BACKTEST: {self.symbol} ({self.lookback_days}d @ {self.timeframe})")
        print(f"{'='*80}\n")

        # 1) Fetch OHLCV (extra bars for indicator warmup)
        warmup = 200
        try:
            print(f"[1/4] Fetching data...")
            df = get_binance_data(self.symbol, timeframe=self.timeframe, limit=self.lookback_days + warmup)
            if df is None or len(df) < 100:
                print("❌ Insufficient data")
                return None
        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            return None

        # 2) Compute indicators once
        print(f"[2/4] Computing indicators...")
        df = self._prepare_indicators(df)

        # 3) Evaluate signals per bar and simulate outcomes
        print(f"[3/4] Generating signals and simulating trades...")
        start_idx = self._first_valid_index(df)
        start_idx = max(start_idx, len(df) - self.lookback_days)  # restrict to requested lookback

        for i in range(start_idx, len(df) - 1):  # avoid last bar for lookahead
            analysis = self._build_analysis_at(df, i)
            if not analysis:
                continue
            # Relaxed thresholds to increase signal frequency in backtests
            signal = generate_trade_signal_simple(
                analysis,
                rsi_low=self.rule_params['rsi_low'],
                rsi_high=self.rule_params['rsi_high'],
                adx_min=self.rule_params['adx_min'],
                require_macd=self.rule_params['require_macd'],
            )
            trade = self._simulate_trade(df, i, signal, lookahead=20)
            if trade:
                self.trades.append(trade)

        # 4) Summarize
        print(f"[4/4] Calculating results...")
        wins = [t for t in self.trades if t.pnl > 0]
        losses = [t for t in self.trades if t.pnl < 0]
        total = len(self.trades)
        win_rate = (len(wins) / total * 100) if total else 0.0
        avg_pnl_pct = sum(t.pnl_pct for t in self.trades) / total if total else 0.0

        self.summary = {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'period_days': self.lookback_days,
            'trades': total,
            'wins': len(wins),
            'losses': len(losses),
            'win_rate_pct': round(win_rate, 2),
            'avg_pnl_pct': round(avg_pnl_pct, 3),
            'tp_hits': sum(1 for t in self.trades if t.exit_reason == 'TP1'),
            'sl_hits': sum(1 for t in self.trades if t.exit_reason == 'SL'),
        }

        print("\n✅ Backtest Complete!")
        print(f"   Trades: {self.summary['trades']}")
        print(f"   Win Rate: {self.summary['win_rate_pct']}%")
        print(f"   Avg P&L per trade: {self.summary['avg_pnl_pct']}%\n")

        return self.summary


def main():
    """Example usage"""
    backtester = Backtester('LAB/USDT:USDT', lookback_days=180)
    results = backtester.backtest()
    if results:
        print(results)


if __name__ == "__main__":
    main()
