#!/usr/bin/env python3
"""
Signal Analysis Tool - Check if TP or SL was hit first
"""

import ccxt
import re
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Initialize exchanges
bybit = ccxt.bybit({'enableRateLimit': True})
mexc = ccxt.mexc({'enableRateLimit': True})

def parse_signals(filepath):
    """Parse signals from telegram export text file"""
    with open(filepath, 'r') as f:
        lines = f.readlines()

    signals = []
    current_signal = {}

    for i, line in enumerate(lines):
        # Detect start of trade signal
        direction_match = re.search(r'(🟢|🔴) \*(LONG|SHORT) ([A-Z]+/USDT:USDT)\*', line)
        if direction_match:
            # Start new signal
            current_signal = {
                'direction': direction_match.group(2),
                'symbol': direction_match.group(3)
            }
            continue

        # Extract entry price
        if '💰 Entry:' in line or 'Entry:' in line:
            entry_match = re.search(r'`([\d.]+)`', line)
            if entry_match:
                current_signal['entry'] = float(entry_match.group(1))

        # Extract stop loss
        if '🛑 Stop Loss:' in line or 'Stop Loss:' in line:
            sl_match = re.search(r'`([\d.]+)`', line)
            if sl_match:
                current_signal['stop_loss'] = float(sl_match.group(1))

        # Extract take profit
        if '🎯 Take Profit:' in line or 'Take Profit:' in line:
            tp_match = re.search(r'`([\d.]+)`', line)
            if tp_match:
                current_signal['take_profit'] = float(tp_match.group(1))

        # Extract timestamp
        if '⏰' in line:
            time_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
            if time_match and current_signal:
                current_signal['timestamp'] = time_match.group(1)

                # Check if we have all required fields
                if all(k in current_signal for k in ['symbol', 'direction', 'entry', 'stop_loss', 'take_profit', 'timestamp']):
                    signals.append(current_signal.copy())
                    current_signal = {}

    return signals


def get_exchange_for_symbol(symbol):
    """Determine which exchange to use for a symbol"""
    bybit_pairs = ['ADA/USDT:USDT', 'AVAX/USDT:USDT', 'ICP/USDT:USDT', 'IRYS/USDT:USDT']

    if symbol in bybit_pairs:
        return bybit
    else:
        return mexc


def analyze_signal(signal):
    """Check if TP or SL was hit first"""

    symbol = signal['symbol']
    direction = signal['direction']
    entry = signal['entry']
    sl = signal['stop_loss']
    tp = signal['take_profit']
    entry_time = datetime.strptime(signal['timestamp'], '%Y-%m-%d %H:%M:%S')

    # Get exchange
    exchange = get_exchange_for_symbol(symbol)

    try:
        # Fetch candles from entry time onwards (15m timeframe)
        since = int(entry_time.timestamp() * 1000)
        candles = exchange.fetch_ohlcv(symbol, '15m', since=since, limit=200)

        if not candles:
            return None

        # Check each candle
        for candle in candles:
            timestamp, open_price, high, low, close, volume = candle
            candle_time = datetime.fromtimestamp(timestamp / 1000)

            if direction == 'LONG':
                # Check if SL hit (low went below SL)
                if low <= sl:
                    return {
                        'result': 'SL HIT',
                        'hit_time': candle_time,
                        'hit_price': sl,
                        'pnl_pct': ((sl - entry) / entry) * 100
                    }
                # Check if TP hit (high went above TP)
                elif high >= tp:
                    return {
                        'result': 'TP HIT',
                        'hit_time': candle_time,
                        'hit_price': tp,
                        'pnl_pct': ((tp - entry) / entry) * 100
                    }

            elif direction == 'SHORT':
                # Check if SL hit (high went above SL)
                if high >= sl:
                    return {
                        'result': 'SL HIT',
                        'hit_time': candle_time,
                        'hit_price': sl,
                        'pnl_pct': ((entry - sl) / entry) * -100
                    }
                # Check if TP hit (low went below TP)
                elif low <= tp:
                    return {
                        'result': 'TP HIT',
                        'hit_time': candle_time,
                        'hit_price': tp,
                        'pnl_pct': ((entry - tp) / entry) * 100
                    }

        # Neither hit yet - check current price
        current = candles[-1][4]  # Close price

        if direction == 'LONG':
            current_pnl = ((current - entry) / entry) * 100
        else:
            current_pnl = ((entry - current) / entry) * 100

        return {
            'result': 'OPEN',
            'hit_time': None,
            'hit_price': current,
            'pnl_pct': current_pnl
        }

    except Exception as e:
        return {
            'result': 'ERROR',
            'error': str(e)
        }


def main():
    print("\n" + "="*100)
    print("🔍 SIGNAL ANALYSIS - TP vs SL Hit Analysis")
    print("="*100 + "\n")

    # Parse signals
    filepath = '/home/behar/Desktop/Text File (5).txt'
    signals = parse_signals(filepath)

    print(f"📊 Found {len(signals)} signals to analyze\n")
    print("Analyzing...\n")

    # Analyze each signal
    results = []

    for i, signal in enumerate(signals, 1):
        print(f"[{i}/{len(signals)}] {signal['symbol']} {signal['direction']}...", end=" ", flush=True)

        analysis = analyze_signal(signal)

        if analysis:
            signal['analysis'] = analysis
            results.append(signal)

            if analysis['result'] == 'TP HIT':
                print(f"✅ TP HIT ({analysis['pnl_pct']:+.2f}%)")
            elif analysis['result'] == 'SL HIT':
                print(f"❌ SL HIT ({analysis['pnl_pct']:+.2f}%)")
            elif analysis['result'] == 'OPEN':
                print(f"🔄 OPEN ({analysis['pnl_pct']:+.2f}%)")
            else:
                print(f"⚠️  {analysis.get('error', 'Unknown')}")
        else:
            print("❌ Failed")

    # Summary
    print("\n" + "="*100)
    print("📊 ANALYSIS RESULTS")
    print("="*100 + "\n")

    tp_hits = [r for r in results if r['analysis']['result'] == 'TP HIT']
    sl_hits = [r for r in results if r['analysis']['result'] == 'SL HIT']
    open_trades = [r for r in results if r['analysis']['result'] == 'OPEN']

    print(f"✅ TP Hit: {len(tp_hits)}")
    print(f"❌ SL Hit: {len(sl_hits)}")
    print(f"🔄 Still Open: {len(open_trades)}")
    print(f"📊 Total Analyzed: {len(results)}")

    if len(tp_hits) + len(sl_hits) > 0:
        win_rate = (len(tp_hits) / (len(tp_hits) + len(sl_hits))) * 100
        print(f"\n🎯 Win Rate: {win_rate:.1f}%")

    # Calculate total PnL
    total_pnl = sum([r['analysis']['pnl_pct'] for r in results if r['analysis']['result'] in ['TP HIT', 'SL HIT']])
    if tp_hits or sl_hits:
        avg_pnl = total_pnl / (len(tp_hits) + len(sl_hits))
        print(f"💰 Average PnL per Trade: {avg_pnl:+.2f}%")
        print(f"💵 Total PnL (Closed): {total_pnl:+.2f}%")

    # Detailed results
    print("\n" + "="*100)
    print("📋 DETAILED RESULTS")
    print("="*100 + "\n")

    # Group by symbol
    by_symbol = {}
    for r in results:
        sym = r['symbol']
        if sym not in by_symbol:
            by_symbol[sym] = []
        by_symbol[sym].append(r)

    for symbol in sorted(by_symbol.keys()):
        trades = by_symbol[symbol]
        tp_count = len([t for t in trades if t['analysis']['result'] == 'TP HIT'])
        sl_count = len([t for t in trades if t['analysis']['result'] == 'SL HIT'])
        open_count = len([t for t in trades if t['analysis']['result'] == 'OPEN'])

        if tp_count + sl_count > 0:
            symbol_wr = (tp_count / (tp_count + sl_count)) * 100
            print(f"\n{symbol}:")
            print(f"  Total: {len(trades)} | TP: {tp_count} | SL: {sl_count} | Open: {open_count} | WR: {symbol_wr:.1f}%")

            for trade in trades:
                a = trade['analysis']
                entry_time = trade['timestamp']

                if a['result'] == 'TP HIT':
                    time_diff = a['hit_time'] - datetime.strptime(entry_time, '%Y-%m-%d %H:%M:%S')
                    print(f"    ✅ {trade['direction']} @ {trade['entry']:.6f} → TP {trade['take_profit']:.6f} | +{a['pnl_pct']:.2f}% | {time_diff}")
                elif a['result'] == 'SL HIT':
                    time_diff = a['hit_time'] - datetime.strptime(entry_time, '%Y-%m-%d %H:%M:%S')
                    print(f"    ❌ {trade['direction']} @ {trade['entry']:.6f} → SL {trade['stop_loss']:.6f} | {a['pnl_pct']:.2f}% | {time_diff}")
                elif a['result'] == 'OPEN':
                    print(f"    🔄 {trade['direction']} @ {trade['entry']:.6f} → Current {a['hit_price']:.6f} | {a['pnl_pct']:+.2f}%")

    print("\n" + "="*100)


if __name__ == "__main__":
    main()
