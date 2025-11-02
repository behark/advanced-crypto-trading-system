#!/usr/bin/env python3
"""
Unified Stock Screener
Combines TradingView fundamentals + Custom Indicators + SuperBuySellTrend

Usage:
    ./run_screener.py                    # Quality growth with SBST
    ./run_screener.py momentum           # Momentum with SBST
    ./run_screener.py sbst-only          # SBST signals only
    ./run_screener.py custom             # Custom filters
"""
import sys
from screener import screen_with_custom_indicators, print_results


def strategy_quality_growth_sbst():
    """
    Strategy 1: Quality Growth + SBST Confirmation
    
    Looking for:
    - Healthy fundamentals (from TradingView MCP)
    - Strong technical indicators
    - SBST uptrend confirmation
    """
    print("="*80)
    print("STRATEGY: Quality Growth + SuperBuySellTrend")
    print("="*80)
    print("\nLooking for quality stocks in confirmed uptrends with good technicals")
    print()
    
    # Start with quality candidates (you'd get these from TradingView MCP)
    candidates = [
        'AAPL', 'MSFT', 'GOOGL', 'NVDA', 'META',
        'AMZN', 'TSLA', 'AMD', 'NFLX', 'CRM',
        'ADBE', 'ORCL', 'CSCO', 'AVGO', 'QCOM'
    ]
    
    filters = {
        # Technical filters
        'rsi_min': 35,
        'rsi_max': 70,
        'min_adx': 15,
        
        # SBST filters
        'sbst_uptrend': True,
        'sbst_confirmed': True,  # Both levels must agree
    }
    
    print("Filters:")
    for key, value in filters.items():
        print(f"  - {key}: {value}")
    print()
    
    results = screen_with_custom_indicators(
        candidates,
        custom_filters=filters,
        include_sbst=True,
        max_workers=5
    )
    
    print_results(results, show_sbst=True)
    return results


def strategy_momentum_breakout():
    """
    Strategy 2: Momentum Breakout + SBST Buy Signal
    
    Looking for:
    - Strong momentum
    - Recent SBST buy signal
    - High trend strength (ADX)
    """
    print("\n" + "="*80)
    print("STRATEGY: Momentum Breakout + SBST Buy Signals")
    print("="*80)
    print("\nLooking for momentum stocks with recent SBST buy signals")
    print()
    
    candidates = [
        'PLTR', 'COIN', 'MARA', 'RIOT', 'SQ',
        'SNOW', 'DKNG', 'SHOP', 'NET', 'CRWD',
        'ZS', 'OKTA', 'DDOG', 'MDB', 'FTNT'
    ]
    
    filters = {
        # Momentum filters
        'rsi_min': 50,
        'rsi_max': 75,
        'min_adx': 25,
        'macd_bullish': True,
        
        # SBST filters
        'sbst_uptrend': True,
        'sbst_buy_signal': True,  # Recent buy signal
    }
    
    print("Filters:")
    for key, value in filters.items():
        print(f"  - {key}: {value}")
    print()
    
    results = screen_with_custom_indicators(
        candidates,
        custom_filters=filters,
        include_sbst=True,
        max_workers=5
    )
    
    print_results(results, show_sbst=True)
    return results


def strategy_sbst_only():
    """
    Strategy 3: SBST Signals Only
    
    Pure trend following based on SuperBuySellTrend
    """
    print("\n" + "="*80)
    print("STRATEGY: SuperBuySellTrend Pure Signals")
    print("="*80)
    print("\nLooking for any stocks with confirmed SBST uptrends")
    print()
    
    # Larger universe
    candidates = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA',
        'BRK-B', 'JPM', 'V', 'MA', 'UNH', 'HD', 'PG',
        'DIS', 'NFLX', 'PYPL', 'INTC', 'AMD', 'CRM',
        'BA', 'GE', 'F', 'GM', 'AAL'
    ]
    
    filters = {
        'sbst_uptrend': True,
        'sbst_confirmed': True,
    }
    
    print("Filters:")
    for key, value in filters.items():
        print(f"  - {key}: {value}")
    print()
    
    results = screen_with_custom_indicators(
        candidates,
        custom_filters=filters,
        include_sbst=True,
        max_workers=10
    )
    
    print_results(results, show_sbst=True)
    return results


def strategy_custom(rsi_min=35, rsi_max=70, sbst_uptrend=True, sbst_confirmed=True):
    """
    Strategy 4: Custom Filters
    
    Customize your own screening criteria
    """
    print("\n" + "="*80)
    print("STRATEGY: Custom Filters")
    print("="*80)
    print()
    
    candidates = [
        'AAPL', 'MSFT', 'GOOGL', 'NVDA', 'META',
        'AMZN', 'TSLA', 'AMD', 'NFLX', 'CRM',
    ]
    
    filters = {
        'rsi_min': rsi_min,
        'rsi_max': rsi_max,
        'sbst_uptrend': sbst_uptrend,
        'sbst_confirmed': sbst_confirmed,
    }
    
    print("Custom Filters:")
    for key, value in filters.items():
        print(f"  - {key}: {value}")
    print()
    
    results = screen_with_custom_indicators(
        candidates,
        custom_filters=filters,
        include_sbst=True,
        max_workers=5
    )
    
    print_results(results, show_sbst=True)
    return results


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        strategy = sys.argv[1].lower()
    else:
        strategy = 'quality'
    
    if strategy == 'momentum':
        strategy_momentum_breakout()
    elif strategy == 'sbst-only' or strategy == 'sbst':
        strategy_sbst_only()
    elif strategy == 'custom':
        strategy_custom()
    else:
        strategy_quality_growth_sbst()
    
    print("\n" + "="*80)
    print("Screening complete!")
    print("="*80)
    print("\nAvailable strategies:")
    print("  ./run_screener.py                # Quality growth + SBST")
    print("  ./run_screener.py momentum       # Momentum + SBST buy signals")
    print("  ./run_screener.py sbst-only      # Pure SBST trend following")
    print("  ./run_screener.py custom         # Custom filters")


if __name__ == "__main__":
    main()
