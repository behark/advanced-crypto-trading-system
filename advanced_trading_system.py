#!/usr/bin/env python3
"""
Advanced Trading System - Complete Integration
Combines all features: Multi-TF, Weighted Confidence, Divergence Detection, Risk Management
"""

import time
import signal
import sys
from datetime import datetime

from binance_crypto import (
    analyze_crypto_binance,
    generate_trade_signal,
    get_multi_timeframe_analysis,
    validate_signal_multi_timeframe,
    calculate_weighted_confidence,
    detect_divergences,
)
from risk_management import RiskManager, RiskProfile


# Global flag for graceful shutdown
running = True


def signal_handler(sig, frame):
    """Handle CTRL+C gracefully"""
    global running
    print("\n\n🛑 Shutdown signal received. Stopping after current analysis...")
    running = False


class AdvancedTradingSystem:
    """Complete trading system with all optimization features"""
    
    def __init__(self, account_balance=10000, win_rate=0.55, avg_win_loss_ratio=1.5):
        """Initialize advanced trading system"""
        self.profile = RiskProfile(
            account_balance=account_balance,
            max_risk_per_trade=0.02,
            max_portfolio_heat=0.06,
            max_drawdown=0.20,
            confidence_threshold=75,
            win_rate=win_rate,
            avg_win_loss_ratio=avg_win_loss_ratio,
        )
        self.risk_manager = RiskManager(self.profile)
    
    def analyze_symbol_advanced(self, symbol, base_timeframe="5m", verbose=True):
        """Perform complete advanced analysis on a symbol"""
        if verbose:
            print(f"\n{'='*80}\nADVANCED TRADING ANALYSIS: {symbol}\n{'='*80}\n")
            print("[1/4] Analyzing base timeframe...")
        
        analysis_5m = analyze_crypto_binance(symbol, timeframe=base_timeframe)
        if not analysis_5m:
            print("❌ Failed to fetch data")
            return None
        
        if verbose:
            print("[2/4] Generating signal...")
        signal_5m = generate_trade_signal(analysis_5m, use_weighted_confidence=True)
        
        if verbose:
            print("[3/4] Fetching multi-timeframe data...")
        multi_tf_analyses = get_multi_timeframe_analysis(symbol, base_timeframe)
        
        if verbose:
            print("[4/4] Validating across timeframes...")
        tf_validation = validate_signal_multi_timeframe(signal_5m, multi_tf_analyses)
        
        return {
            'symbol': symbol,
            'base_timeframe': base_timeframe,
            'analysis_5m': analysis_5m,
            'signal_5m': signal_5m,
            'multi_tf_analyses': multi_tf_analyses,
            'multi_tf_validation': tf_validation,
            'divergences': signal_5m.get('divergences', []),
            'weighted_confidence': signal_5m.get('weighted_confidence', 0),
        }
    
    def validate_and_size_trade(self, signal, entry, stop_loss, symbol="UNKNOWN"):
        """Complete trade validation and position sizing"""
        if not signal or signal['action'] == 'WAIT':
            return {'approved': False, 'reason': 'No valid signal'}
        
        confidence = signal.get('confidence', 0)
        validation = self.risk_manager.validate_trade(entry, stop_loss, confidence, symbol)
        
        if not validation['approved']:
            return validation
        
        sizing = self.risk_manager.calculate_position_size(entry, stop_loss, confidence)
        
        return {
            'approved': validation['approved'],
            'reasons': validation['reasons'],
            'warnings': validation['warnings'],
            'risk_score': validation['risk_score'],
            'sizing': sizing,
            'entry': entry,
            'stop_loss': stop_loss,
            'position_size': sizing['recommended_size'],
            'risk_dollars': sizing['risk_dollars'],
            'kelly_fraction': sizing['kelly_fraction'],
        }
    
    def print_complete_analysis(self, analysis):
        """Print complete trading analysis"""
        print(f"\n{'='*80}\nCOMPLETE ANALYSIS: {analysis['symbol']}\n{'='*80}\n")
        
        signal = analysis['signal_5m']
        print(f"5M SIGNAL: {signal['action']} (Confidence: {signal['confidence']}%)")
        print(f"Weighted Confidence: {analysis['weighted_confidence']:.1f}%\n")
        
        if analysis['divergences']:
            print(f"⚠️  DIVERGENCES ({len(analysis['divergences'])}):")
            for div in analysis['divergences']:
                print(f"  - {div['type']}: {div['description']}")
            print()
        
        tf_val = analysis['multi_tf_validation']
        print(f"MULTI-TIMEFRAME VALIDATION:")
        print(f"  Strength: {tf_val['strength']:.0f}%")
        print(f"  Confirmations: {tf_val['confirmations']}/3")
        print(f"  Approved: {'✅ YES' if tf_val['approved'] else '❌ NO'}")
        if tf_val['timeframes_aligned']:
            print(f"  Aligned: {', '.join(tf_val['timeframes_aligned'])}")
        
        print(f"\nRISK ASSESSMENT:")
        entry = signal.get('entry') or 0
        stop_loss = signal.get('stop_loss') or 0
        print(f"  Entry: ${entry:.8f}")
        print(f"  Stop: ${stop_loss:.8f}")
        if entry > 0 and stop_loss > 0:
            risk_pct = abs((stop_loss - entry) / entry * 100)
            print(f"  Risk: {risk_pct:.3f}%")
        rr = signal.get('risk_reward') or 0
        print(f"  R:R: 1:{rr:.2f}")
        
        print(f"\n{'='*80}")
        if tf_val['approved'] and signal['action'] != 'WAIT':
            print("✅ STRONG SIGNAL - Multi-TF Confirmed")
        elif signal['action'] != 'WAIT':
            print("⚠️  WEAK SIGNAL - Consider higher TF entry")
        else:
            print("⏸️  NO CLEAR SIGNAL")
        print(f"{'='*80}\n")
    
    def get_risk_report(self):
        """Get risk management report"""
        return self.risk_manager.get_risk_report()


def run_single_analysis(system, symbol="LAB/USDT:USDT", base_timeframe="5m"):
    """Run a single analysis iteration"""
    analysis = system.analyze_symbol_advanced(symbol, base_timeframe=base_timeframe)

    if analysis:
        system.print_complete_analysis(analysis)

        signal = analysis['signal_5m']
        if signal['action'] != 'WAIT':
            print("TRADE VALIDATION & SIZING\n" + "="*80 + "\n")

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
                for r in trade_info['reasons']:
                    print(f"  {r}")
            else:
                print("❌ TRADE REJECTED\n")
                for r in trade_info['reasons']:
                    print(f"  {r}")

            print(f"\n{'='*80}\nPORTFOLIO RISK REPORT\n{'='*80}")
            report = system.get_risk_report()
            print(f"Balance: ${report['account_balance']:.2f}")
            print(f"Drawdown: {report['current_drawdown']*100:.2f}%")
            print(f"Heat: {report['portfolio_heat']*100:.2f}%")
            print(f"Status: {report['status']}\n")


def main(continuous=False, interval=60, symbol="LAB/USDT:USDT", base_timeframe="5m", clear_screen=False):
    """
    Main function with optional continuous mode

    Args:
        continuous: If True, runs indefinitely until stopped
        interval: Seconds to wait between runs (only in continuous mode)
        symbol: Trading symbol to analyze
        base_timeframe: Base timeframe for analysis
        clear_screen: If True, clears screen between runs
    """
    global running

    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    system = AdvancedTradingSystem(
        account_balance=10000,
        win_rate=0.55,
        avg_win_loss_ratio=1.5
    )

    if continuous:
        print(f"🔄 Starting continuous monitoring (every {interval}s)")
        print("Press CTRL+C to stop gracefully\n")

        iteration = 0
        while running:
            iteration += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if clear_screen and iteration > 1:
                print("\033[2J\033[H")  # Clear screen

            print(f"\n{'='*80}")
            print(f"ITERATION #{iteration} - {timestamp}")
            print(f"{'='*80}")

            try:
                run_single_analysis(system, symbol, base_timeframe)
            except Exception as e:
                print(f"\n❌ Error during analysis: {e}")
                print("Continuing to next iteration...\n")

            if running:
                print(f"\n⏳ Waiting {interval} seconds until next analysis...")
                print(f"   (Press CTRL+C to stop)")

                # Sleep in small increments to allow quick response to CTRL+C
                for _ in range(interval):
                    if not running:
                        break
                    time.sleep(1)

        print("\n✅ Monitoring stopped successfully.")
    else:
        # Single run mode
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{'='*80}")
        print(f"SINGLE RUN - {timestamp}")
        print(f"{'='*80}")
        run_single_analysis(system, symbol, base_timeframe)


if __name__ == "__main__":
    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(description='Advanced Trading System')
    parser.add_argument('-c', '--continuous', action='store_true',
                        help='Run continuously instead of once')
    parser.add_argument('-i', '--interval', type=int, default=60,
                        help='Interval between runs in seconds (default: 60)')
    parser.add_argument('-s', '--symbol', type=str, default='LAB/USDT:USDT',
                        help='Trading symbol (default: LAB/USDT:USDT)')
    parser.add_argument('-t', '--timeframe', type=str, default='5m',
                        help='Base timeframe (default: 5m)')
    parser.add_argument('--clear', action='store_true',
                        help='Clear screen between runs')

    args = parser.parse_args()

    main(
        continuous=args.continuous,
        interval=args.interval,
        symbol=args.symbol,
        base_timeframe=args.timeframe,
        clear_screen=args.clear
    )
