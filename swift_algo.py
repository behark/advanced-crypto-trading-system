"""
Swift Algo Accurate - Fixed
Professional trading indicator with multi-timeframe support, EMA crossovers, 
zone management, and advanced signal filtering

Converted from Pine Script to Python
"""
import pandas as pd
import numpy as np
import pandas_ta as ta


def calculate_swift_algo(df, 
                        ema_fast1=9, ema_fast2=21, ema_slow=50, trend_ma=200,
                        rsi_length=14, rsi_oversold=30, rsi_overbought=70,
                        atr_length=14, adx_length=14, adx_threshold=20,
                        vol_multiplier=1.3, min_signal_gap=5,
                        stop_loss_atr=1.5, risk_reward=2.0):
    """
    Calculate Swift Algo indicator with all features
    
    Args:
        df: DataFrame with OHLCV data
        ema_fast1: Fast EMA 1 period (default 9)
        ema_fast2: Fast EMA 2 period (default 21)
        ema_slow: Slow EMA period (default 50)
        trend_ma: Trend MA period (default 200)
        rsi_length: RSI period (default 14)
        rsi_oversold: RSI oversold level (default 30)
        rsi_overbought: RSI overbought level (default 70)
        atr_length: ATR period (default 14)
        adx_length: ADX period (default 14)
        adx_threshold: ADX threshold for sideways (default 20)
        vol_multiplier: Volume multiplier (default 1.3)
        min_signal_gap: Minimum bars between signals (default 5)
        stop_loss_atr: Stop loss ATR multiplier (default 1.5)
        risk_reward: Risk/Reward ratio (default 2.0)
    
    Returns:
        DataFrame with all Swift Algo indicators
    """
    df = df.copy()
    
    # === EMAs ===
    df['ema9'] = ta.ema(df['Close'], length=ema_fast1)
    df['ema21'] = ta.ema(df['Close'], length=ema_fast2)
    df['ema50'] = ta.ema(df['Close'], length=ema_slow)
    df['sma200'] = ta.sma(df['Close'], length=trend_ma)
    
    # === RSI & ATR ===
    df['rsi'] = ta.rsi(df['Close'], length=rsi_length)
    df['atr'] = ta.atr(df['High'], df['Low'], df['Close'], length=atr_length)
    
    # === Volume ===
    df['avg_volume'] = ta.sma(df['Volume'], length=20)
    df['high_volume'] = (df['Volume'] > df['avg_volume'] * vol_multiplier).astype(int)
    
    # === ADX for Trend Strength ===
    adx = ta.adx(df['High'], df['Low'], df['Close'], length=adx_length)
    df['adx'] = adx['ADX_' + str(adx_length)]
    df['is_sideways'] = (df['adx'] < adx_threshold).astype(int)
    
    # === TREND DETECTION ===
    # Current Timeframe
    df['ema_sorted'] = ((df['ema9'] > df['ema21']) & 
                        (df['ema21'] > df['ema50']) & 
                        (df['Close'] > df['sma200'])).astype(int)
    
    df['ctf_bullish'] = df['ema_sorted']
    df['ctf_bearish'] = ((df['ema9'] < df['ema21']) & 
                         (df['ema21'] < df['ema50']) & 
                         (df['Close'] < df['sma200'])).astype(int)
    
    df['strong_bullish'] = df['ctf_bullish']
    df['strong_bearish'] = df['ctf_bearish']
    
    # === SIGNALS ===
    # EMA Crossovers
    df['ema_cross_up'] = ta.cross(df['ema9'], df['ema21'])
    df['ema_cross_down'] = ta.cross(df['ema21'], df['ema9'])
    df['ema_med_cross_up'] = ta.cross(df['ema21'], df['ema50'])
    df['ema_med_cross_down'] = ta.cross(df['ema50'], df['ema21'])
    
    # Trend starts
    df['trend_start_bull'] = df['strong_bullish'].astype(int) & ~df['strong_bullish'].shift(1).fillna(0).astype(int)
    df['trend_start_bear'] = df['strong_bearish'].astype(int) & ~df['strong_bearish'].shift(1).fillna(0).astype(int)
    
    # RSI Filters
    df['rsi_neutral'] = ((df['rsi'] > rsi_oversold) & (df['rsi'] < rsi_overbought)).astype(int)
    
    # Buy Conditions
    df['buy_cond1'] = (df['ema_cross_up'].astype(int) & 
                       df['strong_bullish'].astype(int) & 
                       df['rsi_neutral'].astype(int) & 
                       df['high_volume'].astype(int)).astype(bool)
    
    df['buy_cond2'] = (df['ema_med_cross_up'].astype(int) & 
                       df['strong_bullish'].astype(int) & 
                       (df['rsi'] > 40).astype(int)).astype(bool)
    
    df['buy_cond3'] = (df['trend_start_bull'].astype(int) & 
                       (df['Close'] > df['Open']).astype(int) & 
                       df['high_volume'].astype(int) & 
                       (df['rsi'] > 35).astype(int)).astype(bool)
    
    df['long_signal_raw'] = (df['buy_cond1'] | df['buy_cond2'] | df['buy_cond3']) & df['strong_bullish'].astype(bool)
    
    # Sell Conditions
    df['sell_cond1'] = (df['ema_cross_down'].astype(int) & 
                        df['strong_bearish'].astype(int) & 
                        df['rsi_neutral'].astype(int) & 
                        df['high_volume'].astype(int)).astype(bool)
    
    df['sell_cond2'] = (df['ema_med_cross_down'].astype(int) & 
                        df['strong_bearish'].astype(int) & 
                        (df['rsi'] < 60).astype(int)).astype(bool)
    
    df['sell_cond3'] = (df['trend_start_bear'].astype(int) & 
                        (df['Close'] < df['Open']).astype(int) & 
                        df['high_volume'].astype(int) & 
                        (df['rsi'] < 65).astype(int)).astype(bool)
    
    df['short_signal_raw'] = (df['sell_cond1'] | df['sell_cond2'] | df['sell_cond3']) & df['strong_bearish'].astype(bool)
    
    # === REVERSAL SIGNALS ===
    df['bearish_reversal'] = (df['strong_bullish'].shift(1).fillna(0).astype(bool) & 
                              ta.cross(df['Close'], df['ema21'], above=False) & 
                              (df['rsi'] > 65).astype(int)).astype(bool)
    
    df['bullish_reversal'] = (df['strong_bearish'].shift(1).fillna(0).astype(bool) & 
                              ta.cross(df['Close'], df['ema21'], above=True) & 
                              (df['rsi'] < 35).astype(int)).astype(bool)
    
    # === SIGNAL FILTERING ===
    # Track last signals
    last_long_bars = np.zeros(len(df), dtype=int)
    last_short_bars = np.zeros(len(df), dtype=int)
    last_reversal_bars = np.zeros(len(df), dtype=int)
    
    last_long = 0
    last_short = 0
    last_reversal = 0
    
    for i in range(len(df)):
        if df['long_signal_raw'].iloc[i]:
            last_long = i
        if df['short_signal_raw'].iloc[i]:
            last_short = i
        if df['bearish_reversal'].iloc[i] or df['bullish_reversal'].iloc[i]:
            last_reversal = i
        
        last_long_bars[i] = i - last_long
        last_short_bars[i] = i - last_short
        last_reversal_bars[i] = i - last_reversal
    
    df['last_long_bars'] = last_long_bars
    df['last_short_bars'] = last_short_bars
    df['last_reversal_bars'] = last_reversal_bars
    
    # Apply filters
    df['filtered_long_signal'] = (df['long_signal_raw'] & 
                                  (df['last_long_bars'] >= min_signal_gap) & 
                                  (df['last_short_bars'] >= min_signal_gap)).astype(bool)
    
    df['filtered_short_signal'] = (df['short_signal_raw'] & 
                                   (df['last_short_bars'] >= min_signal_gap) & 
                                   (df['last_long_bars'] >= min_signal_gap)).astype(bool)
    
    df['filtered_bearish_reversal'] = (df['bearish_reversal'] & 
                                       (df['last_reversal_bars'] > min_signal_gap)).astype(bool)
    
    df['filtered_bullish_reversal'] = (df['bullish_reversal'] & 
                                       (df['last_reversal_bars'] > min_signal_gap)).astype(bool)
    
    # Signal strength
    df['is_strong_long'] = (df['filtered_long_signal'] & 
                            (df['buy_cond2'] | df['buy_cond3'])).astype(bool)
    
    df['is_strong_short'] = (df['filtered_short_signal'] & 
                             (df['sell_cond2'] | df['sell_cond3'])).astype(bool)
    
    # === TP/SL LEVELS ===
    df['long_stop_loss'] = 0.0
    df['long_tp'] = 0.0
    df['short_stop_loss'] = 0.0
    df['short_tp'] = 0.0
    
    for i in range(len(df)):
        if df['filtered_long_signal'].iloc[i]:
            entry = df['Close'].iloc[i]
            sl = entry - (df['atr'].iloc[i] * stop_loss_atr)
            tp = entry + (df['atr'].iloc[i] * stop_loss_atr * risk_reward)
            df.at[i, 'long_stop_loss'] = sl
            df.at[i, 'long_tp'] = tp
        
        if df['filtered_short_signal'].iloc[i]:
            entry = df['Close'].iloc[i]
            sl = entry + (df['atr'].iloc[i] * stop_loss_atr)
            tp = entry - (df['atr'].iloc[i] * stop_loss_atr * risk_reward)
            df.at[i, 'short_stop_loss'] = sl
            df.at[i, 'short_tp'] = tp
    
    return df


def get_swift_algo_signals(symbol, period="6mo", **kwargs):
    """
    Get Swift Algo signals for a symbol
    
    Returns:
        Dict with latest Swift Algo data
    """
    import yfinance as yf
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        
        if len(df) < 50:
            return None
        
        df = calculate_swift_algo(df, **kwargs)
        
        latest = df.iloc[-1]
        
        # Check for recent signals
        recent_long = df['filtered_long_signal'].iloc[-5:].any()
        recent_short = df['filtered_short_signal'].iloc[-5:].any()
        recent_bull_rev = df['filtered_bullish_reversal'].iloc[-5:].any()
        recent_bear_rev = df['filtered_bearish_reversal'].iloc[-5:].any()
        
        signals = {
            'symbol': symbol,
            'close': latest['Close'],
            
            # EMAs
            'ema9': latest['ema9'],
            'ema21': latest['ema21'],
            'ema50': latest['ema50'],
            'sma200': latest['sma200'],
            
            # Trend
            'strong_bullish': bool(latest['strong_bullish']),
            'strong_bearish': bool(latest['strong_bearish']),
            'is_sideways': bool(latest['is_sideways']),
            
            # Technicals
            'rsi': latest['rsi'],
            'atr': latest['atr'],
            'adx': latest['adx'],
            'high_volume': bool(latest['high_volume']),
            
            # Signals
            'long_signal': bool(latest['filtered_long_signal']),
            'short_signal': bool(latest['filtered_short_signal']),
            'strong_long': bool(latest['is_strong_long']),
            'strong_short': bool(latest['is_strong_short']),
            'bullish_reversal': bool(latest['filtered_bullish_reversal']),
            'bearish_reversal': bool(latest['filtered_bearish_reversal']),
            
            # Recent signals
            'recent_long': recent_long,
            'recent_short': recent_short,
            'recent_bull_rev': recent_bull_rev,
            'recent_bear_rev': recent_bear_rev,
            
            # TP/SL
            'long_tp': latest['long_tp'],
            'long_sl': latest['long_stop_loss'],
            'short_tp': latest['short_tp'],
            'short_sl': latest['short_stop_loss'],
        }
        
        return signals
        
    except Exception as e:
        print(f"Error calculating Swift Algo for {symbol}: {e}")
        return None


if __name__ == "__main__":
    import yfinance as yf
    
    # Test
    symbol = "AAPL"
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="6mo")
    
    df = calculate_swift_algo(df)
    
    print(f"\nSwift Algo Analysis for {symbol}")
    print("="*60)
    
    latest = df.iloc[-1]
    print(f"Close: ${latest['Close']:.2f}")
    print(f"Trend: {'BULLISH' if latest['strong_bullish'] else 'BEARISH' if latest['strong_bearish'] else 'SIDEWAYS'}")
    print(f"RSI: {latest['rsi']:.2f}")
    print(f"ADX: {latest['adx']:.2f}")
    print(f"Volume: {'HIGH' if latest['high_volume'] else 'NORMAL'}")
    print(f"Long Signal: {latest['filtered_long_signal']}")
    print(f"Short Signal: {latest['filtered_short_signal']}")
    print(f"Strong Long: {latest['is_strong_long']}")
    print(f"Strong Short: {latest['is_strong_short']}")
    
    # Show recent signals
    print(f"\nRecent Long Signals (last 5): {df['filtered_long_signal'].iloc[-5:].sum()}")
    print(f"Recent Short Signals (last 5): {df['filtered_short_signal'].iloc[-5:].sum()}")
