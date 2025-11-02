"""
Chandelier Exit Indicator
Converted from Pine Script by Alex Orekhov (everget)

Professional stop-loss and reversal indicator using ATR and highest/lowest
"""
import pandas as pd
import numpy as np
import pandas_ta as ta


def calculate_chandelier_exit(df, length=22, mult=3.0, use_close=True):
    """
    Calculate Chandelier Exit indicator
    
    Args:
        df: DataFrame with OHLC data
        length: ATR period (default 22)
        mult: ATR multiplier (default 3.0)
        use_close: Use close price for extremums (default True)
    
    Returns:
        DataFrame with Chandelier Exit columns
    """
    df = df.copy()
    
    # Calculate ATR
    atr = mult * ta.atr(df['High'], df['Low'], df['Close'], length=length)
    
    n = len(df)
    long_stop = np.zeros(n)
    short_stop = np.zeros(n)
    direction = np.zeros(n, dtype=int)
    
    # Initialize
    direction[0] = 1
    
    for i in range(n):
        # Calculate highest and lowest
        if i < length:
            if use_close:
                highest = df['Close'].iloc[:i+1].max()
                lowest = df['Close'].iloc[:i+1].min()
            else:
                highest = df['High'].iloc[:i+1].max()
                lowest = df['Low'].iloc[:i+1].min()
        else:
            if use_close:
                highest = df['Close'].iloc[i-length+1:i+1].max()
                lowest = df['Close'].iloc[i-length+1:i+1].min()
            else:
                highest = df['High'].iloc[i-length+1:i+1].max()
                lowest = df['Low'].iloc[i-length+1:i+1].min()
        
        # Calculate stops
        long_stop_temp = highest - atr.iloc[i]
        short_stop_temp = lowest + atr.iloc[i]
        
        # Apply previous stop rules
        if i > 0:
            long_stop_prev = long_stop[i-1]
            short_stop_prev = short_stop[i-1]
            
            # Long stop can't go lower
            long_stop[i] = max(long_stop_temp, long_stop_prev) if df['Close'].iloc[i-1] > long_stop_prev else long_stop_temp
            
            # Short stop can't go higher
            short_stop[i] = min(short_stop_temp, short_stop_prev) if df['Close'].iloc[i-1] < short_stop_prev else short_stop_temp
        else:
            long_stop[i] = long_stop_temp
            short_stop[i] = short_stop_temp
        
        # Determine direction
        if i == 0:
            direction[i] = 1
        else:
            long_stop_prev = long_stop[i-1]
            short_stop_prev = short_stop[i-1]
            
            if df['Close'].iloc[i] > short_stop_prev:
                direction[i] = 1
            elif df['Close'].iloc[i] < long_stop_prev:
                direction[i] = -1
            else:
                direction[i] = direction[i-1]
    
    # Detect signals
    buy_signal = np.zeros(n, dtype=bool)
    sell_signal = np.zeros(n, dtype=bool)
    
    for i in range(1, n):
        if direction[i] == 1 and direction[i-1] == -1:
            buy_signal[i] = True
        if direction[i] == -1 and direction[i-1] == 1:
            sell_signal[i] = True
    
    # Add to dataframe
    df['ce_long_stop'] = long_stop
    df['ce_short_stop'] = short_stop
    df['ce_direction'] = direction
    df['ce_buy_signal'] = buy_signal
    df['ce_sell_signal'] = sell_signal
    
    return df


def get_chandelier_exit_signals(symbol, period="6mo", length=22, mult=3.0):
    """
    Get Chandelier Exit signals for a symbol
    
    Returns:
        Dict with latest Chandelier Exit data
    """
    import yfinance as yf
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        
        if len(df) < length + 10:
            return None
        
        df = calculate_chandelier_exit(df, length=length, mult=mult)
        
        latest = df.iloc[-1]
        
        # Check for recent signals
        recent_buy = df['ce_buy_signal'].iloc[-5:].any()
        recent_sell = df['ce_sell_signal'].iloc[-5:].any()
        
        signals = {
            'symbol': symbol,
            'close': latest['Close'],
            'ce_long_stop': latest['ce_long_stop'],
            'ce_short_stop': latest['ce_short_stop'],
            'ce_direction': 'LONG' if latest['ce_direction'] == 1 else 'SHORT',
            'ce_buy_signal': bool(latest['ce_buy_signal']),
            'ce_sell_signal': bool(latest['ce_sell_signal']),
            'ce_recent_buy': recent_buy,
            'ce_recent_sell': recent_sell,
            'ce_distance_to_stop': abs(latest['Close'] - (latest['ce_long_stop'] if latest['ce_direction'] == 1 else latest['ce_short_stop'])),
        }
        
        return signals
        
    except Exception as e:
        print(f"Error calculating Chandelier Exit for {symbol}: {e}")
        return None
