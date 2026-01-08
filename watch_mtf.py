#!/usr/bin/env python3
"""
Watch a symbol and alert when multi-timeframe alignment occurs.
Conditions (defaults):
- confidence >= --min_conf (default 70)
- weighted_confidence >= --min_wconf (default 70)
- multi-timeframe confirmations >= 2 (15m/1h/4h)

Usage examples:
  ./venv/bin/python watch_mtf.py --symbol MINA/USDT --timeframe 5m
  ./venv/bin/python watch_mtf.py --symbol LAB/USDT:USDT --timeframe 5m --min_conf 70 --min_wconf 70 --interval 300 --max_iter 60
"""
import argparse
import time
import sys
from datetime import datetime

sys.path.append('.')
from binance_crypto import (
    analyze_crypto_binance,
    generate_trade_signal,
    get_multi_timeframe_analysis,
    validate_signal_multi_timeframe,
)

def run_once(symbol: str, timeframe: str, min_conf: int, min_wconf: int):
    analysis = analyze_crypto_binance(symbol, timeframe=timeframe)
    if not analysis:
        return {'status': 'no_data'}
    signal = generate_trade_signal(analysis)
    mtf = get_multi_timeframe_analysis(symbol, base_timeframe=timeframe)
    val = validate_signal_multi_timeframe(signal, mtf)

    meets = (
        signal.get('confidence', 0) >= min_conf and
        signal.get('weighted_confidence', 0) >= min_wconf and
        val.get('confirmations', 0) >= 2
    )
    return {
        'ts': str(analysis['timestamp']),
        'symbol': symbol,
        'timeframe': timeframe,
        'meets': meets,
        'action': signal.get('action'),
        'confidence': signal.get('confidence'),
        'weighted_confidence': signal.get('weighted_confidence'),
        'confirmations': val.get('confirmations'),
        'aligned': val.get('timeframes_aligned', []),
        'entry': signal.get('entry'),
        'stop': signal.get('stop_loss'),
        'tp1': signal.get('take_profit_1'),
        'tp2': signal.get('take_profit_2'),
        'rr': signal.get('risk_reward'),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--symbol', required=True, help='e.g., MINA/USDT or LAB/USDT:USDT for futures')
    p.add_argument('--timeframe', default='5m')
    p.add_argument('--min_conf', type=int, default=70)
    p.add_argument('--min_wconf', type=int, default=70)
    p.add_argument('--interval', type=int, default=300, help='seconds between checks')
    p.add_argument('--max_iter', type=int, default=60, help='number of iterations before exit')
    args = p.parse_args()

    for i in range(1, args.max_iter + 1):
        res = run_once(args.symbol, args.timeframe, args.min_conf, args.min_wconf)
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        if res.get('status') == 'no_data':
            print(f"[{now}] {args.symbol} {args.timeframe} - no data")
        else:
            prefix = 'ALERT' if res['meets'] else 'STATUS'
            print(
                f"[{now}] {prefix} {args.symbol} {args.timeframe} "
                f"{res['action']} conf={res['confidence']} w={res['weighted_confidence']} "
                f"mtf={res['confirmations']} aligned={','.join(res['aligned']) if res['aligned'] else '-'}"
            )
            if res['meets']:
                print(
                    f"  Entry={res['entry']} SL={res['stop']} TP1={res['tp1']} TP2={res['tp2']} R:R={res['rr']}\n"
                )
        if i < args.max_iter:
            time.sleep(args.interval)

if __name__ == '__main__':
    main()
