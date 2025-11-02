"""
TradingView MCP Integration Module
Wrapper to combine TradingView MCP screener with custom indicators

NOTE: This module is designed to be called from Warp Agent Mode
where the MCP tools are available. It won't work standalone.
"""
import json


# Example: How to use this with Warp Agent Mode MCP tools
USAGE_EXAMPLE = """
# In Warp Agent Mode, you can:

1. Use TradingView MCP to get fundamental screener results:
   - Call screen_stocks with fundamental filters (ROE, P/E, etc.)
   - Get list of quality stocks

2. Pass those symbols to screener.py:
   - Apply custom technical indicator filters
   - Get final filtered list with both fundamental + technical criteria

Example workflow:
```python
# Step 1: Get quality stocks from TradingView (via Warp Agent MCP)
# This would be done via call_mcp_tool in Warp:
# {
#   "name": "screen_stocks",
#   "input": {
#     "filters": [
#       {"field": "return_on_equity", "operator": "greater", "value": 15},
#       {"field": "debt_to_equity", "operator": "less", "value": 0.5}
#     ],
#     "limit": 50
#   }
# }

# Step 2: Extract symbols from results
tv_symbols = [stock['symbol'] for stock in tv_results['data']]

# Step 3: Apply custom technical filters
from screener import screen_with_custom_indicators

custom_filters = {
    'rsi_min': 40,
    'rsi_max': 65,
    'require_uptrend': True,
    'min_adx': 20,
}

final_results = screen_with_custom_indicators(tv_symbols, custom_filters)
```
"""


def extract_symbols_from_mcp_result(mcp_result):
    """
    Extract symbol list from MCP screen_stocks result
    
    Args:
        mcp_result: JSON result from MCP screen_stocks call
    
    Returns:
        List of ticker symbols
    """
    try:
        if isinstance(mcp_result, str):
            mcp_result = json.loads(mcp_result)
        
        # Handle different possible result structures
        if 'data' in mcp_result:
            data = mcp_result['data']
        elif 'results' in mcp_result:
            data = mcp_result['results']
        else:
            data = mcp_result
        
        # Extract symbols
        symbols = []
        for item in data:
            if 's' in item:  # TradingView format: 's' = symbol
                # Extract just the ticker part (e.g., "NASDAQ:AAPL" -> "AAPL")
                symbol = item['s'].split(':')[-1]
                symbols.append(symbol)
            elif 'symbol' in item:
                symbol = item['symbol'].split(':')[-1]
                symbols.append(symbol)
        
        return symbols
    
    except Exception as e:
        print(f"Error extracting symbols: {e}")
        return []


def format_mcp_filters(simple_filters):
    """
    Convert simple filter dict to TradingView MCP format
    
    Args:
        simple_filters: Dict like {'roe_min': 15, 'pe_max': 20}
    
    Returns:
        List of filter objects for MCP
    """
    filter_mapping = {
        'roe_min': ('return_on_equity', 'greater'),
        'roe_max': ('return_on_equity', 'less'),
        'pe_min': ('price_earnings_ttm', 'greater'),
        'pe_max': ('price_earnings_ttm', 'less'),
        'debt_equity_max': ('debt_to_equity', 'less'),
        'net_margin_min': ('net_margin_ttm', 'greater'),
        'revenue_growth_min': ('total_revenue_yoy_growth_ttm', 'greater'),
        'market_cap_min': ('market_cap_basic', 'greater'),
        'volume_min': ('volume', 'greater'),
    }
    
    mcp_filters = []
    for key, value in simple_filters.items():
        if key in filter_mapping:
            field, operator = filter_mapping[key]
            mcp_filters.append({
                'field': field,
                'operator': operator,
                'value': value
            })
    
    return mcp_filters


# Predefined screening strategies
SCREENING_STRATEGIES = {
    'quality_growth_conservative': {
        'tv_filters': {
            'roe_min': 15,
            'debt_equity_max': 0.5,
            'net_margin_min': 12,
            'revenue_growth_min': 8,
        },
        'custom_filters': {
            'rsi_min': 40,
            'rsi_max': 65,
            'require_uptrend': True,
            'min_adx': 20,
            'macd_bullish': True,
        },
        'description': 'High-quality, profitable, growing companies with strong technical momentum'
    },
    
    'value_recovery': {
        'tv_filters': {
            'pe_max': 15,
            'debt_equity_max': 1.0,
            'roe_min': 10,
        },
        'custom_filters': {
            'rsi_min': 30,
            'rsi_max': 50,
            'require_uptrend': True,
            'min_adx': 15,
        },
        'description': 'Undervalued stocks showing signs of technical recovery'
    },
    
    'momentum_breakout': {
        'tv_filters': {
            'revenue_growth_min': 15,
            'market_cap_min': 1e9,  # $1B+
        },
        'custom_filters': {
            'rsi_min': 60,
            'rsi_max': 80,
            'min_adx': 25,
            'macd_bullish': True,
            'require_uptrend': True,
        },
        'description': 'High-growth stocks breaking out with strong momentum'
    },
    
    'dividend_quality': {
        'tv_filters': {
            'roe_min': 12,
            'debt_equity_max': 0.7,
            # Note: dividend_yield would need to be added to filter_mapping
        },
        'custom_filters': {
            'rsi_min': 35,
            'rsi_max': 65,
            'require_uptrend': True,
            'min_adx': 15,
        },
        'description': 'Quality dividend stocks with stable trends'
    }
}


def get_strategy(strategy_name):
    """Get a predefined screening strategy"""
    return SCREENING_STRATEGIES.get(strategy_name)


def list_strategies():
    """List all available screening strategies"""
    print("\nAvailable Screening Strategies:")
    print("=" * 80)
    for name, strategy in SCREENING_STRATEGIES.items():
        print(f"\n{name}:")
        print(f"  Description: {strategy['description']}")
        print(f"  TradingView Filters: {strategy['tv_filters']}")
        print(f"  Custom Filters: {strategy['custom_filters']}")


if __name__ == "__main__":
    print(USAGE_EXAMPLE)
    print("\n" + "="*80)
    list_strategies()
