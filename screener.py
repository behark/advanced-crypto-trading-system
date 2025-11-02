"""
Combined Stock Screener
Integrates TradingView fundamental data with custom technical indicators
"""
import json
from indicators import get_latest_signals
from super_buy_sell_trend import get_latest_sbst_signals
from concurrent.futures import ThreadPoolExecutor, as_completed


def get_combined_signals(symbol, include_sbst=True):
    """
    Get both standard indicators and SBST signals for a symbol
    
    Returns:
        Dict with all indicator values
    """
    signals = get_latest_signals(symbol)
    
    if signals and include_sbst:
        sbst_signals = get_latest_sbst_signals(symbol)
        if sbst_signals:
            # Add SBST data with prefix
            signals['sbst_trend'] = sbst_signals['trend']
            signals['sbst_trend_confirmed'] = sbst_signals['trend_confirmed']
            signals['sbst_buy_signal'] = sbst_signals['buy_signal']
            signals['sbst_sell_signal'] = sbst_signals['sell_signal']
            signals['sbst_buy_confirm'] = sbst_signals['buy_confirm']
            signals['sbst_sell_confirm'] = sbst_signals['sell_confirm']
            signals['sbst_recent_buy'] = sbst_signals['recent_buy']
            signals['sbst_recent_sell'] = sbst_signals['recent_sell']
            signals['sbst_up_level'] = sbst_signals['up_level']
            signals['sbst_dn_level'] = sbst_signals['dn_level']
    
    return signals


def screen_with_custom_indicators(tv_stocks, custom_filters=None, max_workers=5, include_sbst=True):
    """
    Apply custom indicator filters to TradingView screened stocks
    
    Args:
        tv_stocks: List of stock symbols from TradingView screener
        custom_filters: Dict of custom filter criteria (optional)
        max_workers: Number of parallel workers for fetching data
    
    Returns:
        List of stocks with combined data
    """
    if custom_filters is None:
        custom_filters = {
            'rsi_min': 30,
            'rsi_max': 70,
            'require_uptrend': True,
            'min_adx': 20,  # Trend strength
        }
    
    results = []
    
    # Fetch indicator data in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_symbol = {
            executor.submit(get_combined_signals, symbol, include_sbst): symbol 
            for symbol in tv_stocks
        }
        
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                signals = future.result()
                if signals and passes_filters(signals, custom_filters):
                    results.append(signals)
                    sbst_info = f" [SBST: {signals.get('sbst_trend', 'N/A')}]" if include_sbst else ""
                    print(f"✓ {symbol} passed filters{sbst_info}")
                else:
                    print(f"✗ {symbol} filtered out")
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
    
    return results


def passes_filters(signals, filters):
    """Check if a stock passes custom filter criteria"""
    try:
        # RSI filter
        if 'rsi_min' in filters and signals.get('rsi', 0) < filters['rsi_min']:
            return False
        if 'rsi_max' in filters and signals.get('rsi', 100) > filters['rsi_max']:
            return False
        
        # Uptrend filter
        if filters.get('require_uptrend') and not signals.get('is_uptrend', False):
            return False
        
        # ADX filter (trend strength)
        if 'min_adx' in filters and signals.get('adx', 0) < filters['min_adx']:
            return False
        
        # Golden cross filter
        if filters.get('require_golden_cross') and signals.get('golden_cross', 0) != 1:
            return False
        
        # MACD filter
        if filters.get('macd_bullish') and signals.get('macd_hist', 0) <= 0:
            return False
        
        # Stochastic filter
        if 'stoch_max' in filters and signals.get('stoch_k', 100) > filters['stoch_max']:
            return False
        
        # SuperBuySellTrend filters
        if filters.get('sbst_uptrend') and signals.get('sbst_trend') != 'UPTREND':
            return False
        if filters.get('sbst_downtrend') and signals.get('sbst_trend') != 'DOWNTREND':
            return False
        if filters.get('sbst_confirmed') and signals.get('sbst_trend') != signals.get('sbst_trend_confirmed'):
            return False
        if filters.get('sbst_buy_signal') and not signals.get('sbst_recent_buy', False):
            return False
        
        return True
    except Exception as e:
        print(f"Filter error: {e}")
        return False


def format_results(results, sort_by='rsi'):
    """Format and sort screening results"""
    if not results:
        return []
    
    # Sort by specified field
    sorted_results = sorted(
        results, 
        key=lambda x: x.get(sort_by, 0), 
        reverse=(sort_by not in ['rsi', 'close'])
    )
    
    return sorted_results


def print_results(results, show_sbst=True):
    """Print results in a formatted table"""
    if not results:
        print("\nNo stocks passed the filters.")
        return
    
    has_sbst = any('sbst_trend' in stock for stock in results)
    
    if has_sbst and show_sbst:
        print(f"\n{'='*140}")
        print(f"Found {len(results)} stocks matching criteria")
        print(f"{'='*140}")
        print(f"{'Symbol':<8} {'Price':<10} {'RSI':<8} {'MACD':<10} {'ADX':<8} {'Trend':<8} {'SBST':<10} {'SBST Conf':<10} {'Buy':<6}")
        print(f"{'-'*140}")
        
        for stock in results:
            buy_flag = '🟢' if stock.get('sbst_recent_buy') else ''
            print(
                f"{stock['symbol']:<8} "
                f"${stock['close']:<9.2f} "
                f"{stock.get('rsi', 0):<8.1f} "
                f"{stock.get('macd_hist', 0):<10.3f} "
                f"{stock.get('adx', 0):<8.1f} "
                f"{'UP' if stock.get('is_uptrend') else 'DOWN':<8} "
                f"{stock.get('sbst_trend', 'N/A'):<10} "
                f"{stock.get('sbst_trend_confirmed', 'N/A'):<10} "
                f"{buy_flag:<6}"
            )
    else:
        print(f"\n{'='*100}")
        print(f"Found {len(results)} stocks matching criteria")
        print(f"{'='*100}")
        print(f"{'Symbol':<8} {'Price':<10} {'RSI':<8} {'MACD':<10} {'ADX':<8} {'Trend':<8} {'Golden':<8}")
        print(f"{'-'*100}")
        
        for stock in results:
            print(
                f"{stock['symbol']:<8} "
                f"${stock['close']:<9.2f} "
                f"{stock.get('rsi', 0):<8.1f} "
                f"{stock.get('macd_hist', 0):<10.3f} "
                f"{stock.get('adx', 0):<8.1f} "
                f"{'UP' if stock.get('is_uptrend') else 'DOWN':<8} "
                f"{'YES' if stock.get('golden_cross') == 1 else 'NO':<8}"
            )


def example_quality_growth_screen():
    """
    Example: Screen quality growth stocks with custom technical filters
    
    This would typically start with TradingView screener results,
    then apply custom indicator filters
    """
    print("Example: Quality Growth + Custom Technical Screener")
    print("=" * 60)
    
    # Example list - in real use, get this from TradingView MCP screener
    # For demo, using common quality stocks
    tv_candidates = [
        'AAPL', 'MSFT', 'GOOGL', 'NVDA', 'META',
        'AMZN', 'TSLA', 'AMD', 'NFLX', 'CRM'
    ]
    
    print(f"\nStarting with {len(tv_candidates)} candidates from TradingView screener")
    print("Applying custom technical filters...")
    print()
    
    # Define custom filters
    custom_filters = {
        'rsi_min': 40,
        'rsi_max': 65,
        'require_uptrend': True,
        'min_adx': 20,
        'macd_bullish': True,
    }
    
    print("Custom filters:")
    for key, value in custom_filters.items():
        print(f"  - {key}: {value}")
    print()
    
    # Screen with custom indicators
    results = screen_with_custom_indicators(
        tv_candidates, 
        custom_filters=custom_filters,
        max_workers=5
    )
    
    # Format and display results
    results = format_results(results, sort_by='adx')
    print_results(results)
    
    return results


def example_momentum_breakout_screen():
    """
    Example: Momentum breakout screen
    Looking for stocks breaking out with strong momentum
    """
    print("\nExample: Momentum Breakout Screener")
    print("=" * 60)
    
    # Example momentum candidates
    momentum_candidates = [
        'PLTR', 'COIN', 'RIOT', 'MARA', 'SQ',
        'SNOW', 'DKNG', 'SHOP', 'U', 'NET'
    ]
    
    print(f"\nScreening {len(momentum_candidates)} momentum candidates...")
    
    # Breakout filters
    breakout_filters = {
        'rsi_min': 60,
        'rsi_max': 80,
        'min_adx': 25,
        'macd_bullish': True,
        'require_uptrend': True,
    }
    
    print("Breakout filters:")
    for key, value in breakout_filters.items():
        print(f"  - {key}: {value}")
    print()
    
    results = screen_with_custom_indicators(
        momentum_candidates,
        custom_filters=breakout_filters,
        max_workers=5
    )
    
    results = format_results(results, sort_by='rsi')
    print_results(results)
    
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "momentum":
        example_momentum_breakout_screen()
    else:
        example_quality_growth_screen()
