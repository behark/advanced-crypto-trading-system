"""
Nick Rypock Trailing Reverse (NRTR) Indicator
Converted from Pine Script by Alex Orekhov (everget)

Percentage-based trailing stop and reversal indicator
"""
import pandas as pd
import numpy as np


def calculate_nrtr(df, percentage=0.02):
    """
    Calculate NRTR indicator
    
    Args:
        df: DataFrame with OHLC data
        percentage: Coefficient of correction as decimal (default 0.02 = 2%)
    
    Returns:
        DataFrame with NRTR columns
    """
    df = df.copy()
    
    n = len(df)
    trend = np.zeros(n, dtype=int)
    hp = np.zeros(n)  # High point
    lp = np.zeros(n)  # Low point
    nrtr = np.zeros(n)
    
    # Initialize
    trend[0] = 0
    hp[0] = df['Close'].iloc[0]
    lp[0] = df['Close'].iloc[0]
    nrtr[0] = df['Close'].iloc[0]
    
    for i in range(1, n):
        close = df['Close'].iloc[i]
        prev_trend = trend[i-1]
        prev_hp = hp[i-1]
        prev_lp = lp[i-1]
        prev_nrtr = nrtr[i-1]
        
        if prev_trend >= 0:  # In uptrend or starting
            # Update high point if close is higher
            if close > prev_hp:
                hp[i] = close
            else:
                hp[i] = prev_hp
            
            # Calculate NRTR (stop loss for long)
            nrtr[i] = hp[i] * (1 - percentage)
            
            # Check for reversal to downtrend
            if close <= nrtr[i]:
                trend[i] = -1
                lp[i] = close
                nrtr[i] = lp[i] * (1 + percentage)
            else:
                trend[i] = 0
                lp[i] = prev_lp
        else:  # In downtrend
            # Update low point if close is lower
            if close < prev_lp:
                lp[i] = close
            else:
                lp[i] = prev_lp
            
            # Calculate NRTR (stop loss for short)
            nrtr[i] = lp[i] * (1 + percentage)
            
            # Check for reversal to uptrend
            if close > nrtr[i]:
                trend[i] = 1
                hp[i] = close
                nrtr[i] = hp[i] * (1 - percentage)
            else:
                trend[i] = -1
                hp[i] = prev_hp
    
    # Detect signals
    buy_signal = np.zeros(n, dtype=bool)
    sell_signal = np.zeros(n, dtype=bool)
    
    for i in range(1, n):
        if trend[i] == 1 and trend[i-1] == -1:
            buy_signal[i] = True
        if (trend[i] == -1 and trend[i-1] == 0) or (trend[i] == -1 and trend[i-1] == 1):
            sell_signal[i] = True
    
    # Add to dataframe
    df['nrtr_value'] = nrtr
    df['nrtr_trend'] = trend
    df['nrtr_hp'] = hp
    df['nrtr_lp'] = lp
    df['nrtr_buy_signal'] = buy_signal
    df['nrtr_sell_signal'] = sell_signal
    
    return df


def get_nrtr_signals(symbol, period="6mo", percentage=0.02):
    """
    Get NRTR signals for a symbol
    
    Returns:
        Dict with latest NRTR data
    """
    import yfinance as yf
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        
        if len(df) < 10:
            return None
        
        df = calculate_nrtr(df, percentage=percentage)
        
        latest = df.iloc[-1]
        
        # Check for recent signals
        recent_buy = df['nrtr_buy_signal'].iloc[-5:].any()
        recent_sell = df['nrtr_sell_signal'].iloc[-5:].any()
        
        signals = {
            'symbol': symbol,
            'close': latest['Close'],
            'nrtr_value': latest['nrtr_value'],
            'nrtr_trend': 'UPTREND' if latest['nrtr_trend'] == 1 else 'DOWNTREND',
            'nrtr_hp': latest['nrtr_hp'],
            'nrtr_lp': latest['nrtr_lp'],
            'nrtr_buy_signal': bool(latest['nrtr_buy_signal']),
            'nrtr_sell_signal': bool(latest['nrtr_sell_signal']),
            'nrtr_recent_buy': recent_buy,
            'nrtr_recent_sell': recent_sell,
            'nrtr_distance_to_stop': abs(latest['Close'] - latest['nrtr_value']),
            'nrtr_distance_pct': abs((latest['Close'] - latest['nrtr_value']) / latest['nrtr_value'] * 100),
        }
        
        return signals
        
    except Exception as e:
        print(f"Error calculating NRTR for {symbol}: {e}")
        return None
