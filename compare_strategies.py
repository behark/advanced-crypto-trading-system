#!/usr/bin/env python3
"""
Strategy Comparison Tool
Compare simple vs complex signal generation with backtesting
"""

import argparse
from backtester import Backtester
from binance_crypto import get_binance_data, analyze_crypto_simple, generate_trade_signal_simple
from advanced_trading_system import AdvancedTradingSystem


def backtest_simple(symbol, lookback_days=180, timeframe="5m"):
    """Backtest using generate_trade_signal_simple()"""
    print("\n" + "="*80)
    print("TESTING SIMPLE STRATEGY (SBST + RSI + MACD + ADX)")
    print("="*80)

    backtester = Backtester(
        symbol=symbol,
        lookback_days=lookback_days,
        timeframe=timeframe,
        rsi_low=40,
        rsi_high=70,
        adx_min=15,
        require_macd=True
    )

    results = backtester.backtest()

    if results and backtester.trades:
        print(f"\n📊 SIMPLE STRATEGY RESULTS")
        print("-" * 80)
        print(f"Total Trades: {results['trades']}")
        print(f"Wins: {results['wins']} | Losses: {results['losses']}")
        print(f"Win Rate: {results['win_rate_pct']}%")
        print(f"Avg P&L per trade: {results['avg_pnl_pct']}%")
        print(f"TP1 Hits: {results['tp_hits']}")
        print(f"SL Hits: {results['sl_hits']}")
        print(f"Time Exits: {results['trades'] - results['tp_hits'] - results['sl_hits']}")

        # Show sample trades
        print(f"\n📋 LAST 5 TRADES:")
        print("-" * 80)
        for trade in backtester.trades[-5:]:
            emoji = "✅" if trade.pnl > 0 else "❌"
            print(f"{emoji} {trade.date.strftime('%Y-%m-%d %H:%M')} | "
                  f"{trade.action:4s} @ ${trade.entry:.8f} → ${trade.exit:.8f} | "
                  f"P&L: {trade.pnl_pct:+.2f}% | Exit: {trade.exit_reason}")

    return results


def test_live_simple(symbol, timeframe="5m"):
    """Test simple strategy on current live data"""
    print("\n" + "="*80)
    print("LIVE TEST: SIMPLE STRATEGY")
    print("="*80)

    analysis = analyze_crypto_simple(symbol, timeframe=timeframe)

    if analysis:
        signal = generate_trade_signal_simple(
            analysis,
            rsi_low=40,
            rsi_high=70,
            adx_min=15,
            require_macd=True
        )

        print(f"\n📊 CURRENT MARKET STATE")
        print("-" * 80)
        print(f"Price: ${analysis['price']:.8f}")
        print(f"Trend: {analysis['trend']} (Aligned: {analysis['trend_aligned']})")
        print(f"RSI: {analysis['rsi']:.1f}")
        print(f"MACD Hist: {analysis['macd_hist']:.8f}")
        print(f"ADX: {analysis['adx']:.1f}")

        print(f"\n🚦 SIGNAL")
        print("-" * 80)
        print(f"Action: {signal['action']}")
        print(f"Confidence: {signal['confidence']}%")

        if signal['action'] in ['BUY', 'SELL']:
            print(f"\nEntry: ${signal['entry']:.8f}")
            print(f"Stop Loss: ${signal['stop_loss']:.8f}")
            print(f"Take Profit 1: ${signal['take_profit_1']:.8f}")
            print(f"Risk:Reward: 1:{signal['risk_reward']:.2f}")

        if signal['reason']:
            print(f"\nReasons:")
            for reason in signal['reason']:
                print(f"  {reason}")

        return signal

    return None


def test_live_complex(symbol, timeframe="5m"):
    """Test complex strategy on current live data"""
    print("\n" + "="*80)
    print("LIVE TEST: COMPLEX STRATEGY (Multi-Indicator + Multi-TF)")
    print("="*80)

    system = AdvancedTradingSystem(
        account_balance=10000,
        win_rate=0.55,
        avg_win_loss_ratio=1.5
    )

    analysis = system.analyze_symbol_advanced(symbol, base_timeframe=timeframe, verbose=False)

    if analysis:
        system.print_complete_analysis(analysis)

        signal = analysis['signal_5m']
        if signal['action'] != 'WAIT':
            print("\nTRADE VALIDATION & SIZING")
            print("=" * 80)

            trade_info = system.validate_and_size_trade(
                signal,
                signal['entry'],
                signal['stop_loss'],
                symbol
            )

            if trade_info['approved']:
                print("✅ TRADE APPROVED\n")
                print(f"Position Size: {trade_info['position_size']:.2f}")
                print(f"Risk Dollars: ${trade_info['risk_dollars']:.2f}")
                print(f"Kelly: {trade_info['kelly_fraction']*100:.2f}%")
                print(f"Risk Score: {trade_info['risk_score']}/100\n")
            else:
                print("❌ TRADE REJECTED\n")
                for r in trade_info['reasons']:
                    print(f"  {r}")

        return signal

    return None


def compare_both(symbol, lookback_days=180, timeframe="5m"):
    """Run both strategies and compare"""
    print("\n" + "#"*80)
    print("#" + " "*78 + "#")
    print(f"#  STRATEGY COMPARISON: {symbol:^60s}  #")
    print("#" + " "*78 + "#")
    print("#"*80)

    # Backtest simple strategy
    simple_results = backtest_simple(symbol, lookback_days, timeframe)

    # Test both on live data
    print("\n\n")
    simple_signal = test_live_simple(symbol, timeframe)

    print("\n\n")
    complex_signal = test_live_complex(symbol, timeframe)

    # Summary comparison
    print("\n\n" + "="*80)
    print("STRATEGY COMPARISON SUMMARY")
    print("="*80)

    if simple_results:
        print(f"\n📊 SIMPLE STRATEGY (Backtested):")
        print(f"   Trades: {simple_results['trades']}")
        print(f"   Win Rate: {simple_results['win_rate_pct']}%")
        print(f"   Avg P&L: {simple_results['avg_pnl_pct']}%")

    print(f"\n🔴 LIVE SIGNALS:")
    print(f"   Simple:  {simple_signal['action']:4s} ({simple_signal['confidence']}%)")
    print(f"   Complex: {complex_signal['action']:4s} ({complex_signal['confidence']}%)")

    print("\n💡 RECOMMENDATION:")
    if simple_results and simple_results['win_rate_pct'] > 50:
        print("   ✅ Simple strategy shows positive backtest results")
        print("   → Start with simple, add complexity only if needed")
    else:
        print("   ⚠️  Simple strategy needs optimization")
        print("   → Adjust parameters (RSI, ADX thresholds)")

    print()


def main():
    parser = argparse.ArgumentParser(description='Compare Simple vs Complex Trading Strategies')
    parser.add_argument('command', choices=['backtest-simple', 'live-simple', 'live-complex', 'compare'],
                        help='Command to run')
    parser.add_argument('-s', '--symbol', type=str, default='LAB/USDT:USDT',
                        help='Trading symbol (default: LAB/USDT:USDT)')
    parser.add_argument('-d', '--days', type=int, default=180,
                        help='Lookback days for backtest (default: 180)')
    parser.add_argument('-t', '--timeframe', type=str, default='5m',
                        help='Timeframe (default: 5m)')

    args = parser.parse_args()

    if args.command == 'backtest-simple':
        backtest_simple(args.symbol, args.days, args.timeframe)
    elif args.command == 'live-simple':
        test_live_simple(args.symbol, args.timeframe)
    elif args.command == 'live-complex':
        test_live_complex(args.symbol, args.timeframe)
    elif args.command == 'compare':
        compare_both(args.symbol, args.days, args.timeframe)


if __name__ == "__main__":
    main()
