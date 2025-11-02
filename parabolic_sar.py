"""
Parabolic SAR Indicator
Converted from Pine Script by Alex Orekhov (everget)

Stop and Reverse indicator for identifying trend reversals
"""
import pandas as pd
import numpy as np
import pandas_ta as ta


def calculate_parabolic_sar(df, start=0.02, increment=0.02, maximum=0.2):
    """
    Calculate Parabolic SAR indicator
    
    Args:
        df: DataFrame with OHLC data
        start: Initial SAR increment (default 0.02 = 2%)
        increment: SAR acceleration factor (default 0.02)
        maximum: Maximum SAR acceleration (default 0.2 = 20%)
    
    Returns:
        DataFrame with added Parabolic SAR columns
    """
    df = df.copy()
    
    n = len(df)
    psar = np.zeros(n)
    psarl = np.zeros(n)  # SAR long
    psars = np.zeros(n)  # SAR short
    bull = np.ones(n, dtype=bool)  # Bull trend
    af = np.full(n, start)  # Acceleration factor
    hp = np.zeros(n)  # High point
    lp = np.zeros(n)  # Low point
    
    # Initialize
    psar[0] = df['Low'].iloc[0]
    psarl[0] = df['Low'].iloc[0]
    psars[0] = df['High'].iloc[0]
    hp[0] = df['High'].iloc[0]
    lp[0] = df['Low'].iloc[0]
    
    for i in range(1, n):
        if bull[i-1]:
            # In uptrend
            psar[i] = psarl[i-1] + af[i-1] * (hp[i-1] - psarl[i-1])
            
            # SAR cannot be above the prior two lows
            psar[i] = min(psar[i], df['Low'].iloc[i-1], df['Low'].iloc[i-2] if i >= 2 else df['Low'].iloc[i-1])
            
            psarl[i] = psar[i]
            
            # Update high point
            if df['High'].iloc[i] > hp[i-1]:
                hp[i] = df['High'].iloc[i]
                af[i] = min(af[i-1] + increment, maximum)
            else:
                hp[i] = hp[i-1]
                af[i] = af[i-1]
            
            # Check for reversal
            if df['Low'].iloc[i] < psar[i]:
                bull[i] = False
                psar[i] = hp[i-1]
                psars[i] = hp[i-1]
                lp[i] = df['Low'].iloc[i]
                af[i] = start
            else:
                bull[i] = True
                lp[i] = lp[i-1]
        else:
            # In downtrend
            psar[i] = psars[i-1] - af[i-1] * (psars[i-1] - lp[i-1])
            
            # SAR cannot be below the prior two highs
            psar[i] = max(psar[i], df['High'].iloc[i-1], df['High'].iloc[i-2] if i >= 2 else df['High'].iloc[i-1])
            
            psars[i] = psar[i]
            
            # Update low point
            if df['Low'].iloc[i] < lp[i-1]:
                lp[i] = df['Low'].iloc[i]
                af[i] = min(af[i-1] + increment, maximum)
            else:
                lp[i] = lp[i-1]
                af[i] = af[i-1]
            
            # Check for reversal
            if df['High'].iloc[i] > psar[i]:
                bull[i] = True
                psar[i] = lp[i-1]
                psarl[i] = lp[i-1]
                hp[i] = df['High'].iloc[i]
                af[i] = start
            else:
                bull[i] = False
                hp[i] = hp[i-1]
    
    # Detect signals
    buySignal = np.zeros(n, dtype=bool)
    sellSignal = np.zeros(n, dtype=bool)
    
    for i in range(1, n):
        # Buy signal: direction changes from short to long
        if bull[i] and not bull[i-1]:
            buySignal[i] = True
        
        # Sell signal: direction changes from long to short
        if not bull[i] and bull[i-1]:
            sellSignal[i] = True
    
    # Direction: 1 = long, -1 = short
    direction = np.where(bull, 1, -1)
    direction_change = np.zeros(n, dtype=bool)
    for i in range(1, n):
        if direction[i] != direction[i-1]:
            direction_change[i] = True
    
    # Add to dataframe
    df['psar'] = psar
    df['psar_trend'] = direction
    df['psar_af'] = af
    df['psar_buy_signal'] = buySignal
    df['psar_sell_signal'] = sellSignal
    df['psar_direction_change'] = direction_change
    
    return df


def get_parabolic_sar_signals(symbol, period="6mo", start=0.02, increment=0.02, maximum=0.2):
    """
    Get Parabolic SAR signals for a symbol
    
    Returns:
        Dict with latest Parabolic SAR data
    """
    import yfinance as yf
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        
        if len(df) < 10:
            return None
        
        df = calculate_parabolic_sar(df, start=start, increment=increment, maximum=maximum)
        
        latest = df.iloc[-1]
        
        # Check for recent signals
        recent_buy = df['psar_buy_signal'].iloc[-5:].any()
        recent_sell = df['psar_sell_signal'].iloc[-5:].any()
        current_buy = latest['psar_buy_signal']
        current_sell = latest['psar_sell_signal']
        
        signals = {
            'symbol': symbol,
            'close': latest['Close'],
            'psar': latest['psar'],
            'psar_trend': 'UPTREND' if latest['psar_trend'] == 1 else 'DOWNTREND',
            'psar_af': latest['psar_af'],
            'psar_buy_signal': current_buy,
            'psar_sell_signal': current_sell,
            'psar_recent_buy': recent_buy,
            'psar_recent_sell': recent_sell,
            'psar_direction_change': latest['psar_direction_change'],
            'psar_distance': latest['Close'] - latest['psar'],
            'psar_distance_pct': ((latest['Close'] - latest['psar']) / latest['psar'] * 100) if latest['psar'] != 0 else 0,
        }
        
        return signals
        
    except Exception as e:
        print(f"Error calculating Parabolic SAR for {symbol}: {e}")
        return None


if __name__ == "__main__":
    import yfinance as yf
    
    # Test
    symbol = "AAPL"
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="6mo")
    
    df = calculate_parabolic_sar(df)
    
    print(f"\nParabolic SAR Analysis for {symbol}")
    print("="*60)
    
    latest = df.iloc[-1]
    print(f"Close: ${latest['Close']:.2f}")
    print(f"SAR: ${latest['psar']:.2f}")
    print(f"Trend: {'UPTREND' if latest['psar_trend'] == 1 else 'DOWNTREND'}")
    print(f"AF (Acceleration Factor): {latest['psar_af']:.4f}")
    print(f"Buy Signal: {latest['psar_buy_signal']}")
    print(f"Sell Signal: {latest['psar_sell_signal']}")
    print(f"Distance from SAR: ${latest['Close'] - latest['psar']:.4f} ({((latest['Close'] - latest['psar']) / latest['psar'] * 100):.2f}%)")
    
    # Show recent signals
    print(f"\nRecent Buy Signals (last 5): {df['psar_buy_signal'].iloc[-5:].sum()}")
    print(f"Recent Sell Signals (last 5): {df['psar_sell_signal'].iloc[-5:].sum()}")
