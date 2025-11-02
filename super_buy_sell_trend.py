"""
TriexDev - SuperBuySellTrend Indicator
Converted from Pine Script to Python

ATR-based trend following system with two confirmation levels:
- Level 1: ATR Multiplier 1 (0.8) - Initial trend signals
- Level 2: ATR Multiplier 2 (1.6) - Confirmation signals
"""
import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta


def calculate_super_buy_sell_trend(df, periods=10, multiplier1=0.8, multiplier2=1.6, use_atr=True):
    """
    Calculate SuperBuySellTrend indicator
    
    Args:
        df: DataFrame with OHLC data
        periods: ATR period (default 10)
        multiplier1: First ATR multiplier for initial signals (default 0.8)
        multiplier2: Second ATR multiplier for confirmation (default 1.6)
        use_atr: Use standard ATR or simple moving average of TR (default True)
    
    Returns:
        DataFrame with added columns for trend signals
    """
    df = df.copy()
    
    # Source is hl2 (high + low) / 2
    df['src'] = (df['High'] + df['Low']) / 2
    
    # Calculate ATR
    if use_atr:
        df['atr'] = ta.atr(df['High'], df['Low'], df['Close'], length=periods)
    else:
        # Alternative: Simple moving average of true range
        df['tr'] = ta.true_range(df['High'], df['Low'], df['Close'])
        df['atr'] = df['tr'].rolling(window=periods).mean()
    
    # === LEVEL 1: Initial Trend Signals (Multiplier 1) ===
    df['up'] = df['src'] - multiplier1 * df['atr']
    df['dn'] = df['src'] + multiplier1 * df['atr']
    
    # Initialize trend
    trend = []
    up_values = []
    dn_values = []
    
    for i in range(len(df)):
        if i == 0:
            trend.append(1)
            up_values.append(df['up'].iloc[i])
            dn_values.append(df['dn'].iloc[i])
        else:
            # Update up value
            if df['Close'].iloc[i-1] > up_values[i-1]:
                up_val = max(df['up'].iloc[i], up_values[i-1])
            else:
                up_val = df['up'].iloc[i]
            up_values.append(up_val)
            
            # Update dn value
            if df['Close'].iloc[i-1] < dn_values[i-1]:
                dn_val = min(df['dn'].iloc[i], dn_values[i-1])
            else:
                dn_val = df['dn'].iloc[i]
            dn_values.append(dn_val)
            
            # Update trend
            if trend[i-1] == -1 and df['Close'].iloc[i] > dn_values[i-1]:
                trend.append(1)
            elif trend[i-1] == 1 and df['Close'].iloc[i] < up_values[i-1]:
                trend.append(-1)
            else:
                trend.append(trend[i-1])
    
    df['trend'] = trend
    df['up_level'] = up_values
    df['dn_level'] = dn_values
    
    # Buy/Sell signals
    df['buy_signal'] = (df['trend'] == 1) & (df['trend'].shift(1) == -1)
    df['sell_signal'] = (df['trend'] == -1) & (df['trend'].shift(1) == 1)
    
    # === LEVEL 2: Confirmation Signals (Multiplier 2) ===
    df['upx'] = df['src'] - multiplier2 * df['atr']
    df['dnx'] = df['src'] + multiplier2 * df['atr']
    
    trendx = []
    upx_values = []
    dnx_values = []
    
    for i in range(len(df)):
        if i == 0:
            trendx.append(1)
            upx_values.append(df['upx'].iloc[i])
            dnx_values.append(df['dnx'].iloc[i])
        else:
            # Update upx value
            if df['Close'].iloc[i-1] > upx_values[i-1]:
                upx_val = max(df['upx'].iloc[i], upx_values[i-1])
            else:
                upx_val = df['upx'].iloc[i]
            upx_values.append(upx_val)
            
            # Update dnx value
            if df['Close'].iloc[i-1] < dnx_values[i-1]:
                dnx_val = min(df['dnx'].iloc[i], dnx_values[i-1])
            else:
                dnx_val = df['dnx'].iloc[i]
            dnx_values.append(dnx_val)
            
            # Update trendx
            if trendx[i-1] == -1 and df['Close'].iloc[i] > dnx_values[i-1]:
                trendx.append(1)
            elif trendx[i-1] == 1 and df['Close'].iloc[i] < upx_values[i-1]:
                trendx.append(-1)
            else:
                trendx.append(trendx[i-1])
    
    df['trendx'] = trendx
    df['upx_level'] = upx_values
    df['dnx_level'] = dnx_values
    
    # Confirmation signals
    df['buy_confirm'] = (df['trendx'] == 1) & (df['trendx'].shift(1) == -1)
    df['sell_confirm'] = (df['trendx'] == -1) & (df['trendx'].shift(1) == 1)
    
    return df


def get_latest_sbst_signals(symbol, period="6mo", periods=10, multiplier1=0.8, multiplier2=1.6):
    """
    Get latest SuperBuySellTrend signals for a symbol
    
    Returns:
        Dict with current trend status and recent signals
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval="1d")
        
        if len(df) < periods + 1:
            return None
        
        df = calculate_super_buy_sell_trend(df, periods, multiplier1, multiplier2)
        
        latest = df.iloc[-1]
        
        # Check for recent signals (last 5 days)
        recent_buy = df['buy_signal'].iloc[-5:].any()
        recent_sell = df['sell_signal'].iloc[-5:].any()
        recent_buy_confirm = df['buy_confirm'].iloc[-5:].any()
        recent_sell_confirm = df['sell_confirm'].iloc[-5:].any()
        
        signals = {
            'symbol': symbol,
            'close': latest['Close'],
            'trend': 'UPTREND' if latest['trend'] == 1 else 'DOWNTREND',
            'trend_confirmed': 'UPTREND' if latest['trendx'] == 1 else 'DOWNTREND',
            'up_level': latest['up_level'],
            'dn_level': latest['dn_level'],
            'upx_level': latest['upx_level'],
            'dnx_level': latest['dnx_level'],
            'buy_signal': bool(latest['buy_signal']),
            'sell_signal': bool(latest['sell_signal']),
            'buy_confirm': bool(latest['buy_confirm']),
            'sell_confirm': bool(latest['sell_confirm']),
            'recent_buy': recent_buy,
            'recent_sell': recent_sell,
            'recent_buy_confirm': recent_buy_confirm,
            'recent_sell_confirm': recent_sell_confirm,
            'atr': latest['atr'],
        }
        
        return signals
        
    except Exception as e:
        print(f"Error calculating SBST for {symbol}: {e}")
        return None


def screen_with_sbst(symbols, trend_filter='UPTREND', require_confirmation=True, 
                     recent_signal_days=5, max_workers=5):
    """
    Screen stocks using SuperBuySellTrend indicator
    
    Args:
        symbols: List of ticker symbols
        trend_filter: 'UPTREND', 'DOWNTREND', or None for all
        require_confirmation: Require both level 1 and level 2 trends to align
        recent_signal_days: Look for signals within this many days
        max_workers: Parallel workers
    
    Returns:
        List of stocks matching criteria
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_symbol = {
            executor.submit(get_latest_sbst_signals, symbol): symbol 
            for symbol in symbols
        }
        
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                signals = future.result()
                if signals:
                    # Apply filters
                    if trend_filter and signals['trend'] != trend_filter:
                        print(f"✗ {symbol} - Wrong trend direction")
                        continue
                    
                    if require_confirmation and signals['trend'] != signals['trend_confirmed']:
                        print(f"✗ {symbol} - Trend not confirmed")
                        continue
                    
                    results.append(signals)
                    print(f"✓ {symbol} - {signals['trend']} (confirmed: {signals['trend_confirmed']})")
                    
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
    
    return results


def print_sbst_results(results):
    """Print SBST screening results"""
    if not results:
        print("\nNo stocks matched the criteria.")
        return
    
    print(f"\n{'='*120}")
    print(f"Found {len(results)} stocks with SuperBuySellTrend signals")
    print(f"{'='*120}")
    print(f"{'Symbol':<8} {'Price':<10} {'Trend':<12} {'Confirmed':<12} {'Buy Signal':<12} {'Sell Signal':<12} {'ATR':<10}")
    print(f"{'-'*120}")
    
    for stock in results:
        buy_indicator = '🟢 YES' if stock['recent_buy'] else 'No'
        sell_indicator = '🔴 YES' if stock['recent_sell'] else 'No'
        
        print(
            f"{stock['symbol']:<8} "
            f"${stock['close']:<9.2f} "
            f"{stock['trend']:<12} "
            f"{stock['trend_confirmed']:<12} "
            f"{buy_indicator:<12} "
            f"{sell_indicator:<12} "
            f"{stock['atr']:<10.2f}"
        )


if __name__ == "__main__":
    import sys
    
    # Example usage
    print("SuperBuySellTrend Indicator Screener")
    print("="*60)
    
    test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'META', 
                    'TSLA', 'AMD', 'AMZN', 'NFLX', 'CRM']
    
    print(f"\nScreening {len(test_symbols)} stocks for UPTREND signals...\n")
    
    results = screen_with_sbst(
        test_symbols, 
        trend_filter='UPTREND',
        require_confirmation=True,
        max_workers=5
    )
    
    print_sbst_results(results)
    
    # Show details for first result if any
    if results:
        print(f"\n{'='*60}")
        print("Example: Detailed signals for", results[0]['symbol'])
        print(f"{'='*60}")
        for key, value in results[0].items():
            print(f"  {key}: {value}")
