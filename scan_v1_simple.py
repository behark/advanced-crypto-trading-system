#!/usr/bin/env python3
"""
V1 Scanner - Original Simple System
This is the system that gave LAB 90% confidence
Just SBST + SMC, no complexity
"""

import sys
from binance_crypto import analyze_crypto_binance

def scan_v1(symbol):
    """Analyze with V1 system"""
    
    result = analyze_crypto_binance(symbol, timeframe='5m')
    
    print('\n' + '='*80)
    print(f'V1 SYSTEM (ORIGINAL) - {symbol}')
    print('='*80)
    print(f"\n💰 Current Price: ${result.get('current_price', 'N/A')}")
    
    # Determine action
    if result.get('current_buy_confirm'):
        action = 'STRONG BUY'
        confidence = 90
    elif result.get('current_buy_signal'):
        action = 'BUY'
        confidence = 70
    elif result.get('current_sell_signal'):
        action = 'SELL'
        confidence = 70
    else:
        action = 'WAIT'
        confidence = 50
    
    print(f"\n🎯 SIGNAL: {action}")
    print(f"💪 CONFIDENCE: ~{confidence}%")
    
    print("\n📊 SBST INDICATORS:")
    print(f"├─ Trend: {result.get('trend', 'N/A')}")
    print(f"├─ Trend Aligned: {'✅ YES' if result.get('trend_aligned') else '❌ NO'}")
    print(f"├─ Buy Signal: {'✅ YES' if result.get('current_buy_signal') else '❌ NO'}")
    print(f"├─ Buy Confirmed: {'🔥 YES' if result.get('current_buy_confirm') else '❌ NO'}")
    print(f"└─ Sell Signal: {'⚠️ YES' if result.get('current_sell_signal') else '❌ NO'}")
    
    print("\n📈 SMC ANALYSIS:")
    print(f"├─ Bullish Order Block: {'✅ YES' if result.get('smc_bullish_ob') else '❌ NO'}")
    print(f"├─ Bullish FVG: {'✅ YES' if result.get('smc_bullish_fvg') else '❌ NO'}")
    print(f"├─ Liq Sweep Bull: {'✅ YES' if result.get('smc_liq_sweep_bull') else '❌ NO'}")
    print(f"└─ SMC Trend: {result.get('smc_trend', 'N/A')}")
    
    print("\n📊 TECHNICAL:")
    rsi = result.get('rsi')
    macd = result.get('macd_histogram')
    adx = result.get('adx')
    print(f"├─ RSI: {rsi:.1f}" if rsi else "├─ RSI: N/A")
    print(f"├─ MACD Hist: {macd:.4f}" if macd else "├─ MACD: N/A")
    print(f"└─ ADX: {adx:.1f}" if adx else "└─ ADX: N/A")
    
    print('\n' + '='*80)
    
    # Summary
    if action in ['BUY', 'STRONG BUY']:
        print("✅ BULLISH SETUP")
    elif action == 'SELL':
        print("❌ BEARISH SETUP")
    else:
        print("⏸️ NO CLEAR SETUP")
    
    print('='*80 + '\n')
    
    return result


if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'LAB/USDT:USDT'
    scan_v1(symbol)
