#!/usr/bin/env python3
"""
Crypto Trading Signal Generator
Uses SuperBuySellTrend + Technical Indicators for intraday crypto trading
"""
import yfinance as yf
import pandas as pd
from super_buy_sell_trend import calculate_super_buy_sell_trend
from indicators import calculate_rsi, calculate_macd, calculate_moving_averages, calculate_adx


def get_crypto_data(symbol, interval="5m", period="5d"):
    """
    Fetch crypto data for analysis
    
    Args:
        symbol: Crypto symbol (e.g., 'APR-USD' for yfinance format)
        interval: Timeframe ('1m', '5m', '15m', '1h', '4h', '1d')
        period: Lookback period ('1d', '5d', '1mo', '3mo')
    
    Returns:
        DataFrame with OHLCV data
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        return df
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None


def analyze_crypto_signal(symbol, interval="5m", periods=10, multiplier1=0.8, multiplier2=1.6):
    """
    Generate comprehensive trading signal for crypto
    
    Returns:
        Dict with signal analysis
    """
    print(f"\n{'='*80}")
    print(f"CRYPTO ANALYSIS: {symbol}")
    print(f"Timeframe: {interval}")
    print(f"{'='*80}\n")
    
    # Fetch data
    df = get_crypto_data(symbol, interval=interval, period="5d")
    
    if df is None or len(df) < 200:
        print("❌ Insufficient data for analysis")
        return None
    
    print(f"✓ Loaded {len(df)} candles\n")
    
    # Calculate SBST
    df = calculate_super_buy_sell_trend(df, periods=periods, 
                                        multiplier1=multiplier1, 
                                        multiplier2=multiplier2)
    
    # Calculate additional indicators
    df = calculate_rsi(df)
    df = calculate_macd(df)
    df = calculate_moving_averages(df, periods=[10, 20, 50])
    df = calculate_adx(df)
    
    # Get latest values
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    prev_5 = df.iloc[-6] if len(df) >= 6 else df.iloc[0]
    
    # Check for recent signals
    recent_buy = df['buy_signal'].iloc[-5:].any()
    recent_sell = df['sell_signal'].iloc[-5:].any()
    recent_buy_confirm = df['buy_confirm'].iloc[-5:].any()
    recent_sell_confirm = df['sell_confirm'].iloc[-5:].any()
    
    # Current signal
    current_buy = latest['buy_signal']
    current_sell = latest['sell_signal']
    current_buy_confirm = latest['buy_confirm']
    current_sell_confirm = latest['sell_confirm']
    
    # Price momentum
    price_change_5candles = ((latest['Close'] - prev_5['Close']) / prev_5['Close']) * 100
    
    # Trend strength
    trend = 'UPTREND' if latest['trend'] == 1 else 'DOWNTREND'
    trend_confirmed = 'UPTREND' if latest['trendx'] == 1 else 'DOWNTREND'
    trend_aligned = trend == trend_confirmed
    
    # Compile analysis
    analysis = {
        'symbol': symbol,
        'timeframe': interval,
        'timestamp': latest.name,
        'price': latest['Close'],
        'price_change_5c': price_change_5candles,
        
        # SBST signals
        'trend': trend,
        'trend_confirmed': trend_confirmed,
        'trend_aligned': trend_aligned,
        'current_buy_signal': current_buy,
        'current_sell_signal': current_sell,
        'current_buy_confirm': current_buy_confirm,
        'current_sell_confirm': current_sell_confirm,
        'recent_buy': recent_buy,
        'recent_sell': recent_sell,
        'recent_buy_confirm': recent_buy_confirm,
        'recent_sell_confirm': recent_sell_confirm,
        
        # Support/Resistance levels
        'up_level': latest['up_level'],
        'dn_level': latest['dn_level'],
        'upx_level': latest['upx_level'],
        'dnx_level': latest['dnx_level'],
        
        # Technical indicators
        'rsi': latest.get('RSI'),
        'macd': latest.get('MACD_12_26_9'),
        'macd_signal': latest.get('MACDs_12_26_9'),
        'macd_hist': latest.get('MACDh_12_26_9'),
        'adx': latest.get('ADX_14'),
        'ema_10': latest.get('EMA_10'),
        'ema_20': latest.get('EMA_20'),
        'sma_50': latest.get('SMA_50'),
        'atr': latest['atr'],
    }
    
    return analysis


def generate_trade_signal(analysis):
    """
    Generate actionable trade signal with risk management
    
    Returns:
        Dict with trade recommendation
    """
    if not analysis:
        return None
    
    signal = {
        'action': 'WAIT',
        'confidence': 0,
        'reason': [],
        'entry': None,
        'stop_loss': None,
        'take_profit_1': None,
        'take_profit_2': None,
        'risk_reward': None,
    }
    
    price = analysis['price']
    rsi = analysis['rsi']
    macd_hist = analysis['macd_hist']
    adx = analysis['adx']
    
    # === BUY SIGNAL LOGIC ===
    buy_score = 0
    
    if analysis['trend_aligned'] and analysis['trend'] == 'UPTREND':
        buy_score += 3
        signal['reason'].append("✓ Confirmed uptrend (both SBST levels)")
    
    if analysis['current_buy_signal'] or analysis['recent_buy']:
        buy_score += 2
        signal['reason'].append("✓ SBST buy signal triggered")
    
    if analysis['current_buy_confirm'] or analysis['recent_buy_confirm']:
        buy_score += 2
        signal['reason'].append("✓ SBST buy confirmed (Level 2)")
    
    if rsi and 40 < rsi < 70:
        buy_score += 1
        signal['reason'].append(f"✓ RSI healthy ({rsi:.1f})")
    elif rsi and rsi < 30:
        buy_score += 1
        signal['reason'].append(f"✓ RSI oversold ({rsi:.1f}) - potential bounce")
    
    if macd_hist and macd_hist > 0:
        buy_score += 1
        signal['reason'].append("✓ MACD bullish")
    
    if adx and adx > 20:
        buy_score += 1
        signal['reason'].append(f"✓ Strong trend (ADX: {adx:.1f})")
    
    if analysis['price_change_5c'] > 0:
        buy_score += 1
        signal['reason'].append(f"✓ Positive momentum ({analysis['price_change_5c']:.2f}%)")
    
    # === SELL SIGNAL LOGIC ===
    sell_score = 0
    
    if analysis['trend_aligned'] and analysis['trend'] == 'DOWNTREND':
        sell_score += 3
        signal['reason'].append("⚠ Confirmed downtrend (both SBST levels)")
    
    if analysis['current_sell_signal'] or analysis['recent_sell']:
        sell_score += 2
        signal['reason'].append("⚠ SBST sell signal triggered")
    
    if analysis['current_sell_confirm'] or analysis['recent_sell_confirm']:
        sell_score += 2
        signal['reason'].append("⚠ SBST sell confirmed (Level 2)")
    
    if rsi and rsi > 75:
        sell_score += 1
        signal['reason'].append(f"⚠ RSI overbought ({rsi:.1f})")
    
    if macd_hist and macd_hist < 0:
        sell_score += 1
        signal['reason'].append("⚠ MACD bearish")
    
    if analysis['price_change_5c'] < -2:
        sell_score += 1
        signal['reason'].append(f"⚠ Negative momentum ({analysis['price_change_5c']:.2f}%)")
    
    # === DECISION ===
    if buy_score >= 6 and sell_score < 3:
        signal['action'] = 'BUY'
        signal['confidence'] = min(buy_score * 10, 95)
        signal['entry'] = price
        signal['stop_loss'] = analysis['up_level']  # SBST support
        
        # Take profits based on ATR
        atr = analysis['atr']
        signal['take_profit_1'] = price + (atr * 1.5)
        signal['take_profit_2'] = price + (atr * 3.0)
        
        risk = price - signal['stop_loss']
        reward1 = signal['take_profit_1'] - price
        signal['risk_reward'] = reward1 / risk if risk > 0 else 0
        
    elif sell_score >= 6 and buy_score < 3:
        signal['action'] = 'SELL'
        signal['confidence'] = min(sell_score * 10, 95)
        signal['entry'] = price
        signal['stop_loss'] = analysis['dn_level']  # SBST resistance
        
        atr = analysis['atr']
        signal['take_profit_1'] = price - (atr * 1.5)
        signal['take_profit_2'] = price - (atr * 3.0)
        
        risk = signal['stop_loss'] - price
        reward1 = price - signal['take_profit_1']
        signal['risk_reward'] = reward1 / risk if risk > 0 else 0
        
    else:
        signal['action'] = 'WAIT'
        signal['confidence'] = 0
        if not signal['reason']:
            signal['reason'].append("⏸ No clear setup - waiting for better entry")
            signal['reason'].append(f"  Buy score: {buy_score}/11 | Sell score: {sell_score}/11")
    
    return signal


def print_analysis(analysis, signal):
    """Print formatted analysis and trade signal"""
    
    print("📊 MARKET DATA")
    print("-" * 80)
    print(f"Price: ${analysis['price']:.6f}")
    print(f"5-Candle Change: {analysis['price_change_5c']:+.2f}%")
    print(f"ATR: ${analysis['atr']:.6f}")
    print()
    
    print("🎯 SUPERBUYSELLTREND SIGNALS")
    print("-" * 80)
    print(f"Trend Level 1: {analysis['trend']}")
    print(f"Trend Level 2: {analysis['trend_confirmed']}")
    print(f"Alignment: {'✅ ALIGNED' if analysis['trend_aligned'] else '⚠️ NOT ALIGNED'}")
    print(f"Current Buy Signal: {'🟢 YES' if analysis['current_buy_signal'] else 'No'}")
    print(f"Current Sell Signal: {'🔴 YES' if analysis['current_sell_signal'] else 'No'}")
    print(f"Buy Confirmed: {'🟢 YES' if analysis['current_buy_confirm'] else 'No'}")
    print(f"Sell Confirmed: {'🔴 YES' if analysis['current_sell_confirm'] else 'No'}")
    print()
    
    print("📈 TECHNICAL INDICATORS")
    print("-" * 80)
    print(f"RSI (14): {analysis['rsi']:.2f}")
    print(f"MACD Histogram: {analysis['macd_hist']:.6f}")
    print(f"ADX (14): {analysis['adx']:.2f}")
    print(f"EMA 10: ${analysis['ema_10']:.6f}")
    print(f"EMA 20: ${analysis['ema_20']:.6f}")
    print()
    
    print("🎚️ SUPPORT/RESISTANCE LEVELS")
    print("-" * 80)
    print(f"Level 1 Support: ${analysis['up_level']:.6f}")
    print(f"Level 1 Resistance: ${analysis['dn_level']:.6f}")
    print(f"Level 2 Support: ${analysis['upx_level']:.6f}")
    print(f"Level 2 Resistance: ${analysis['dnx_level']:.6f}")
    print()
    
    print("🚦 TRADE SIGNAL")
    print("=" * 80)
    
    if signal['action'] == 'BUY':
        print(f"🟢 {signal['action']} | Confidence: {signal['confidence']}%")
    elif signal['action'] == 'SELL':
        print(f"🔴 {signal['action']} | Confidence: {signal['confidence']}%")
    else:
        print(f"⏸️  {signal['action']}")
    
    print()
    print("Reasoning:")
    for reason in signal['reason']:
        print(f"  {reason}")
    
    if signal['action'] in ['BUY', 'SELL']:
        print()
        print("📋 TRADE PLAN")
        print("-" * 80)
        print(f"Entry: ${signal['entry']:.6f}")
        print(f"Stop Loss: ${signal['stop_loss']:.6f}")
        print(f"Take Profit 1: ${signal['take_profit_1']:.6f} (Risk:Reward = 1:{signal['risk_reward']:.2f})")
        print(f"Take Profit 2: ${signal['take_profit_2']:.6f}")
        
        risk_pct = abs((signal['stop_loss'] - signal['entry']) / signal['entry'] * 100)
        print(f"\nRisk: {risk_pct:.2f}% | Recommended position size: Max 1-2% account risk")
    
    print()


if __name__ == "__main__":
    import sys
    
    # Get symbol from command line or use default
    if len(sys.argv) > 1:
        symbol = sys.argv[1]
    else:
        symbol = "APR-USD"  # APRUSDT in yfinance format
    
    # Get timeframe
    if len(sys.argv) > 2:
        interval = sys.argv[2]
    else:
        interval = "5m"
    
    # Analyze
    analysis = analyze_crypto_signal(symbol, interval=interval, periods=10)
    
    if analysis:
        signal = generate_trade_signal(analysis)
        print_analysis(analysis, signal)
        
        print("\n" + "="*80)
        print("⚠️  DISCLAIMER")
        print("="*80)
        print("This is an automated technical analysis tool, not financial advice.")
        print("Always do your own research and never risk more than you can afford to lose.")
        print("Crypto trading carries significant risk. Past performance doesn't guarantee future results.")
    else:
        print("❌ Could not analyze symbol. Check symbol format and try again.")
        print("\nExamples:")
        print("  python crypto_trader.py BTC-USD 5m")
        print("  python crypto_trader.py ETH-USD 15m")
        print("  python crypto_trader.py APR-USD 5m")
