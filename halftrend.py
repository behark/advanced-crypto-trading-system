"""
HalfTrend Indicator
Converted from Pine Script by Alex Orekhov (everget)

A trend-following indicator that uses ATR channels to identify reversals
"""
import pandas as pd
import numpy as np
import pandas_ta as ta


def calculate_halftrend(df, amplitude=2, channel_deviation=2):
    """
    Calculate HalfTrend indicator
    
    Args:
        df: DataFrame with OHLC data
        amplitude: Lookback period for high/low extremes (default 2)
        channel_deviation: ATR deviation multiplier (default 2)
    
    Returns:
        DataFrame with added HalfTrend columns
    """
    df = df.copy()
    
    # Calculate ATR
    df['atr'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    atr2 = ta.atr(df['High'], df['Low'], df['Close'], length=100) / 2
    
    # Initialize arrays
    n = len(df)
    trend = np.zeros(n, dtype=int)
    nextTrend = np.zeros(n, dtype=int)
    maxLowPrice = np.zeros(n)
    minHighPrice = np.zeros(n)
    up = np.full(n, np.nan)
    down = np.full(n, np.nan)
    atrHigh = np.zeros(n)
    atrLow = np.zeros(n)
    arrowUp = np.full(n, np.nan)
    arrowDown = np.full(n, np.nan)
    ht = np.zeros(n)
    
    # Initial values
    trend[0] = 0
    nextTrend[0] = 0
    maxLowPrice[0] = df['Low'].iloc[0]
    minHighPrice[0] = df['High'].iloc[0]
    
    # Calculate HalfTrend
    for i in range(amplitude, n):
        # Get highest high and lowest low in amplitude period
        high_period = df['High'].iloc[max(0, i-amplitude):i+1]
        low_period = df['Low'].iloc[max(0, i-amplitude):i+1]
        
        highPrice = high_period.max()
        lowPrice = low_period.min()
        
        highma = df['High'].iloc[max(0, i-amplitude):i+1].mean()
        lowma = df['Low'].iloc[max(0, i-amplitude):i+1].mean()
        
        dev = channel_deviation * atr2.iloc[i]
        
        # Trend logic
        if nextTrend[i-1] == 1:
            maxLowPrice[i] = max(lowPrice, maxLowPrice[i-1])
            
            if highma < maxLowPrice[i] and df['Close'].iloc[i] < df['Low'].iloc[i-1]:
                trend[i] = 1
                nextTrend[i] = 0
                minHighPrice[i] = highPrice
            else:
                trend[i] = nextTrend[i-1]
                nextTrend[i] = nextTrend[i-1]
                minHighPrice[i] = minHighPrice[i-1]
                maxLowPrice[i] = maxLowPrice[i-1]
        else:
            minHighPrice[i] = min(highPrice, minHighPrice[i-1])
            
            if lowma > minHighPrice[i] and df['Close'].iloc[i] > df['High'].iloc[i-1]:
                trend[i] = 0
                nextTrend[i] = 1
                maxLowPrice[i] = lowPrice
            else:
                trend[i] = nextTrend[i-1] if i == 0 else trend[i-1]
                nextTrend[i] = nextTrend[i-1] if i == 0 else nextTrend[i-1]
                minHighPrice[i] = minHighPrice[i-1]
                maxLowPrice[i] = maxLowPrice[i-1]
        
        # Calculate up/down levels
        if trend[i] == 0:
            if i > 0 and trend[i-1] != 0:
                up[i] = down[i-1] if not np.isnan(down[i-1]) else down[i-1]
                arrowUp[i] = up[i] - atr2.iloc[i]
            else:
                if i == 0 or np.isnan(up[i-1]):
                    up[i] = maxLowPrice[i]
                else:
                    up[i] = max(maxLowPrice[i], up[i-1])
            
            atrHigh[i] = up[i] + dev
            atrLow[i] = up[i] - dev
            ht[i] = up[i]
        else:
            if i > 0 and trend[i-1] != 1:
                down[i] = up[i-1] if not np.isnan(up[i-1]) else up[i-1]
                arrowDown[i] = down[i] + atr2.iloc[i]
            else:
                if i == 0 or np.isnan(down[i-1]):
                    down[i] = minHighPrice[i]
                else:
                    down[i] = min(minHighPrice[i], down[i-1])
            
            atrHigh[i] = down[i] + dev
            atrLow[i] = down[i] - dev
            ht[i] = down[i]
    
    # Detect signals
    buySignal = np.zeros(n, dtype=bool)
    sellSignal = np.zeros(n, dtype=bool)
    
    for i in range(1, n):
        # Buy signal: trend changes from 1 to 0 with arrow
        if trend[i] == 0 and trend[i-1] == 1 and not np.isnan(arrowUp[i]):
            buySignal[i] = True
        
        # Sell signal: trend changes from 0 to 1 with arrow
        if trend[i] == 1 and trend[i-1] == 0 and not np.isnan(arrowDown[i]):
            sellSignal[i] = True
    
    # Add to dataframe
    df['halftrend'] = ht
    df['halftrend_up'] = up
    df['halftrend_down'] = down
    df['halftrend_atr_high'] = atrHigh
    df['halftrend_atr_low'] = atrLow
    df['halftrend_trend'] = trend
    df['halftrend_buy_signal'] = buySignal
    df['halftrend_sell_signal'] = sellSignal
    
    return df


def get_halftrend_signals(symbol, period="6mo", amplitude=2, channel_deviation=2):
    """
    Get HalfTrend signals for a symbol
    
    Returns:
        Dict with latest HalfTrend data
    """
    import yfinance as yf
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        
        if len(df) < amplitude + 10:
            return None
        
        df = calculate_halftrend(df, amplitude=amplitude, channel_deviation=channel_deviation)
        
        latest = df.iloc[-1]
        
        # Check for recent signals
        recent_buy = df['halftrend_buy_signal'].iloc[-5:].any()
        recent_sell = df['halftrend_sell_signal'].iloc[-5:].any()
        current_buy = latest['halftrend_buy_signal']
        current_sell = latest['halftrend_sell_signal']
        
        signals = {
            'symbol': symbol,
            'close': latest['Close'],
            'halftrend': latest['halftrend'],
            'halftrend_trend': 'UPTREND' if latest['halftrend_trend'] == 0 else 'DOWNTREND',
            'halftrend_atr_high': latest['halftrend_atr_high'],
            'halftrend_atr_low': latest['halftrend_atr_low'],
            'halftrend_buy_signal': current_buy,
            'halftrend_sell_signal': current_sell,
            'halftrend_recent_buy': recent_buy,
            'halftrend_recent_sell': recent_sell,
            'halftrend_distance': latest['Close'] - latest['halftrend'],
            'halftrend_distance_pct': ((latest['Close'] - latest['halftrend']) / latest['halftrend'] * 100) if latest['halftrend'] != 0 else 0,
        }
        
        return signals
        
    except Exception as e:
        print(f"Error calculating HalfTrend for {symbol}: {e}")
        return None


if __name__ == "__main__":
    import yfinance as yf
    
    # Test
    symbol = "AAPL"
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="6mo")
    
    df = calculate_halftrend(df)
    
    print(f"\nHalfTrend Analysis for {symbol}")
    print("="*60)
    
    latest = df.iloc[-1]
    print(f"Close: ${latest['Close']:.2f}")
    print(f"HalfTrend: ${latest['halftrend']:.2f}")
    print(f"Trend: {'UPTREND' if latest['halftrend_trend'] == 0 else 'DOWNTREND'}")
    print(f"Buy Signal: {latest['halftrend_buy_signal']}")
    print(f"Sell Signal: {latest['halftrend_sell_signal']}")
    print(f"ATR High: ${latest['halftrend_atr_high']:.2f}")
    print(f"ATR Low: ${latest['halftrend_atr_low']:.2f}")
    
    # Show recent signals
    print(f"\nRecent Buy Signals (last 5): {df['halftrend_buy_signal'].iloc[-5:].sum()}")
    print(f"Recent Sell Signals (last 5): {df['halftrend_sell_signal'].iloc[-5:].sum()}")
