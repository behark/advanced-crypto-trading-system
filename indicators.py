"""
Custom Technical Indicators Module
Replicates common Pine Script indicators in Python
"""
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np


def get_price_data(symbol, period="6mo", interval="1d"):
    """
    Fetch historical price data for a symbol
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL')
        period: Data period ('1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
        interval: Data interval ('1d', '1h', '1wk', '1mo')
    
    Returns:
        DataFrame with OHLCV data
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None


def calculate_rsi(df, period=14):
    """Calculate RSI (Relative Strength Index)"""
    df['RSI'] = ta.rsi(df['Close'], length=period)
    return df


def calculate_macd(df, fast=12, slow=26, signal=9):
    """Calculate MACD (Moving Average Convergence Divergence)"""
    macd = ta.macd(df['Close'], fast=fast, slow=slow, signal=signal)
    df = pd.concat([df, macd], axis=1)
    return df


def calculate_moving_averages(df, periods=[10, 20, 50, 200]):
    """Calculate multiple SMAs and EMAs"""
    for period in periods:
        df[f'SMA_{period}'] = ta.sma(df['Close'], length=period)
        df[f'EMA_{period}'] = ta.ema(df['Close'], length=period)
    return df


def calculate_bollinger_bands(df, period=20, std=2):
    """Calculate Bollinger Bands"""
    bbands = ta.bbands(df['Close'], length=period, std=std)
    df = pd.concat([df, bbands], axis=1)
    return df


def calculate_atr(df, period=14):
    """Calculate ATR (Average True Range)"""
    df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=period)
    return df


def calculate_stochastic(df, k=14, d=3, smooth_k=3):
    """Calculate Stochastic Oscillator"""
    stoch = ta.stoch(df['High'], df['Low'], df['Close'], k=k, d=d, smooth_k=smooth_k)
    df = pd.concat([df, stoch], axis=1)
    return df


def calculate_adx(df, period=14):
    """Calculate ADX (Average Directional Index)"""
    adx = ta.adx(df['High'], df['Low'], df['Close'], length=period)
    df = pd.concat([df, adx], axis=1)
    return df


def calculate_obv(df):
    """Calculate OBV (On Balance Volume)"""
    df['OBV'] = ta.obv(df['Close'], df['Volume'])
    return df


def golden_cross_check(df):
    """
    Check for golden cross (SMA50 crosses above SMA200)
    Returns: 1 if golden cross, -1 if death cross, 0 otherwise
    """
    if 'SMA_50' not in df.columns or 'SMA_200' not in df.columns:
        calculate_moving_averages(df, periods=[50, 200])
    
    latest = df.iloc[-1]
    previous = df.iloc[-2]
    
    if previous['SMA_50'] <= previous['SMA_200'] and latest['SMA_50'] > latest['SMA_200']:
        return 1  # Golden cross
    elif previous['SMA_50'] >= previous['SMA_200'] and latest['SMA_50'] < latest['SMA_200']:
        return -1  # Death cross
    return 0


def is_uptrend(df, ma_period=50):
    """Check if stock is in uptrend (price above MA and MA sloping up)"""
    if f'SMA_{ma_period}' not in df.columns:
        calculate_moving_averages(df, periods=[ma_period])
    
    latest = df.iloc[-1]
    ma_col = f'SMA_{ma_period}'
    
    # Price above MA and MA is rising
    return latest['Close'] > latest[ma_col] and df[ma_col].iloc[-1] > df[ma_col].iloc[-5]


def calculate_all_indicators(symbol, period="6mo"):
    """
    Calculate all common indicators for a symbol
    
    Returns:
        DataFrame with all indicators, or None if error
    """
    df = get_price_data(symbol, period=period)
    if df is None or len(df) < 200:
        return None
    
    # Calculate all indicators
    df = calculate_rsi(df)
    df = calculate_macd(df)
    df = calculate_moving_averages(df)
    df = calculate_bollinger_bands(df)
    df = calculate_atr(df)
    df = calculate_stochastic(df)
    df = calculate_adx(df)
    df = calculate_obv(df)
    
    return df


def get_latest_signals(symbol, period="6mo"):
    """
    Get latest indicator values for a symbol
    
    Returns:
        Dict with latest indicator values
    """
    df = calculate_all_indicators(symbol, period=period)
    if df is None:
        return None
    
    latest = df.iloc[-1]
    
    signals = {
        'symbol': symbol,
        'close': latest['Close'],
        'rsi': latest.get('RSI'),
        'macd': latest.get('MACD_12_26_9'),
        'macd_signal': latest.get('MACDs_12_26_9'),
        'macd_hist': latest.get('MACDh_12_26_9'),
        'sma_50': latest.get('SMA_50'),
        'sma_200': latest.get('SMA_200'),
        'ema_10': latest.get('EMA_10'),
        'bb_upper': latest.get('BBU_20_2.0'),
        'bb_middle': latest.get('BBM_20_2.0'),
        'bb_lower': latest.get('BBL_20_2.0'),
        'atr': latest.get('ATR'),
        'stoch_k': latest.get('STOCHk_14_3_3'),
        'stoch_d': latest.get('STOCHd_14_3_3'),
        'adx': latest.get('ADX_14'),
        'obv': latest.get('OBV'),
        'golden_cross': golden_cross_check(df),
        'is_uptrend': is_uptrend(df),
        'volume': latest['Volume'],
    }
    
    return signals


if __name__ == "__main__":
    # Example usage
    symbol = "AAPL"
    print(f"Calculating indicators for {symbol}...")
    signals = get_latest_signals(symbol)
    
    if signals:
        print(f"\nLatest signals for {symbol}:")
        for key, value in signals.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
