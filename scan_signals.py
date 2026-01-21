#!/usr/bin/env python3
"""
Quick Signal Scanner - Find high confidence trading signals
"""

from advanced_trading_system import AdvancedTradingSystem
import warnings
import json
import time
from datetime import datetime
import os
from notifications import NotificationManager
warnings.filterwarnings('ignore')

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
TRADING_COUNTRY = os.getenv("TRADING_COUNTRY", "Global")
TIMEFRAME = '1h'  # Trading timeframe
SCAN_INTERVAL_MINUTES = 60  # How often to scan (60 min = 1 hour)

# Pairs to scan (from config_harmonic.yaml)
PAIRS = [
    # Bybit pairs
    'ADA/USDT:USDT',
    'AVAX/USDT:USDT',
    'ICP/USDT:USDT',
    'IRYS/USDT:USDT',
    # MEXC pairs
    'APR/USDT:USDT',
    'BLUAI/USDT:USDT',
    'BOBBOB/USDT:USDT',
    'CLO/USDT:USDT',
    'H/USDT:USDT',
    'JELLYJELLY/USDT:USDT',
    'KITE/USDT:USDT',
    'LAB/USDT:USDT',
    'MINA/USDT:USDT',
    'RIVER/USDT:USDT',
    'VVV/USDT:USDT',
    'ON/USDT:USDT',
    'MON/USDT:USDT',
    'TRC/USDT:USDT',
    'RLS/USDT:USDT',
    'GAIX/USDT:USDT',
    'BEST/USDT:USDT'
]

def send_notifications(message):
    """Send message to all enabled channels."""
    notifier = NotificationManager(
        telegram_bot_token=TELEGRAM_BOT_TOKEN,
        telegram_chat_id=TELEGRAM_CHAT_ID,
        discord_webhook_url=DISCORD_WEBHOOK_URL,
        slack_webhook_url=SLACK_WEBHOOK_URL,
    )
    if not any(notifier.enabled_channels().values()):
        print("⚠️  Notifications disabled (no channels configured).")
        return {}
    return notifier.send(message)

def scan_for_signals(min_confidence=50, timeframe='1h', verbose=True):
    """Scan all pairs for high confidence signals"""

    sys = AdvancedTradingSystem()

    if verbose:
        print("\n" + "="*80)
        print(f"🔥 SCANNING FOR {min_confidence}%+ CONFIDENCE SIGNALS ({timeframe} timeframe)")
        print("="*80 + "\n")

    high_conf = []
    watch_list = []

    for i, pair in enumerate(PAIRS, 1):
        try:
            if verbose:
                print(f"[{i}/{len(PAIRS)}] {pair}...", end=" ", flush=True)
            analysis = sys.analyze_symbol_advanced(pair, base_timeframe=timeframe, verbose=False)

            if analysis:
                signal = analysis['signal_5m']  # Note: key name stays same but uses specified timeframe
                confidence = signal['confidence']
                multi_tf = analysis['multi_tf_validation']['approved']
                
                if confidence >= min_confidence and multi_tf:
                    if verbose:
                        print(f"🔥 {confidence:.1f}% {signal['action']}")
                    high_conf.append({
                        'pair': pair,
                        'signal': signal['action'],
                        'confidence': confidence,
                        'entry': signal['entry'],
                        'stop': signal['stop_loss'],
                        'tp1': signal['take_profit_1'],
                        'tp2': signal['take_profit_2'],
                        'rr': signal['risk_reward']
                    })
                elif 65 <= confidence < min_confidence:
                    if verbose:
                        print(f"⚠️  {confidence:.1f}% {signal['action']}")
                    watch_list.append({
                        'pair': pair,
                        'confidence': confidence,
                        'signal': signal['action']
                    })
                else:
                    if verbose:
                        print(f"⏸️  {confidence:.1f}%")
        except Exception as e:
            if verbose:
                print(f"❌ Error")
    
    # Print results
    if verbose:
        print("\n" + "="*80)
        if high_conf:
            print(f"✅ FOUND {len(high_conf)} TRADEABLE SIGNAL(S)!")
            print("="*80)
            for sig in high_conf:
                print(f"\n🔥 {sig['pair']} - {sig['signal']}")
                print(f"   Confidence: {sig['confidence']:.1f}%")
                print(f"   Entry: ${sig['entry']:.8f}")
                print(f"   Stop: ${sig['stop']:.8f}")
                print(f"   TP1: ${sig['tp1']:.8f}")
                print(f"   TP2: ${sig['tp2']:.8f}")
                print(f"   R:R: {sig['rr']:.2f}")
        else:
            print(f"⏳ NO {min_confidence}%+ SIGNALS FOUND")
            print("="*80)

            if watch_list:
                print(f"\n📊 Watch List (65-{min_confidence-1}%):")
                for sig in watch_list:
                    print(f"   ⚠️  {sig['pair']}: {sig['signal']} ({sig['confidence']:.1f}%)")

            print("\n💡 Keep bot running for automatic alerts!")

        print("\n" + "="*80)

    return high_conf, watch_list


def save_and_notify_signals(high_conf, min_confidence, timeframe, sent_signals):
    """Save signals to JSON and send new ones via notifications"""
    if not high_conf:
        return sent_signals

    # Save signals to JSON file
    scan_data = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'timeframe': timeframe,
        'min_confidence': min_confidence,
        'total_signals': len(high_conf),
        'signals': high_conf
    }

    filename = 'high_confidence_signals.json'
    with open(filename, 'w') as f:
        json.dump(scan_data, f, indent=2)
    print(f"💾 Signals saved to {filename}")

    # Send notifications only for NEW signals
    for sig in high_conf:
        signal_key = f"{sig['pair']}_{sig['signal']}_{sig['confidence']:.1f}"

        # Skip if already sent
        if signal_key in sent_signals:
            continue

        msg = f"🔥 <b>NEW TRADING SIGNAL</b> 🔥\n\n"
        msg += f"💰 <b>{sig['pair']}</b>\n"
        msg += f"📊 Signal: <b>{sig['signal']}</b>\n"
        msg += f"✅ Confidence: <b>{sig['confidence']:.1f}%</b>\n"
        msg += f"⏱ Timeframe: <b>{timeframe}</b>\n"
        msg += f"🌍 Region: <b>{TRADING_COUNTRY}</b>\n\n"
        msg += f"📍 Entry: <code>${sig['entry']:.8f}</code>\n"
        msg += f"🛑 Stop Loss: <code>${sig['stop']:.8f}</code>\n"
        msg += f"🎯 TP1: <code>${sig['tp1']:.8f}</code>\n"
        msg += f"🎯 TP2: <code>${sig['tp2']:.8f}</code>\n"
        msg += f"📈 R:R Ratio: <b>{sig['rr']:.2f}</b>\n\n"
        msg += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        results = send_notifications(msg)
        if any(results.values()):
            print(f"📱 Alert sent for {sig['pair']}")
            sent_signals.add(signal_key)
        else:
            print(f"❌ Failed to send alert for {sig['pair']}")

    return sent_signals


def continuous_scan(min_confidence=50, timeframe='1h', scan_interval_minutes=60):
    """Continuously scan for signals at specified intervals"""
    sent_signals = set()  # Track sent signals to avoid duplicates
    scan_count = 0

    print("\n" + "="*80)
    print("🤖 CONTINUOUS SIGNAL SCANNER STARTED")
    print("="*80)
    print(f"⚙️  Configuration:")
    print(f"   - Timeframe: {timeframe}")
    print(f"   - Min Confidence: {min_confidence}%")
    print(f"   - Scan Interval: {scan_interval_minutes} minutes")
    print(f"   - Monitoring {len(PAIRS)} pairs")
    print(f"\n💡 Press CTRL+C to stop\n")
    print("="*80)

    try:
        while True:
            scan_count += 1
            print(f"\n🔍 Scan #{scan_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            high_conf, watch_list = scan_for_signals(
                min_confidence=min_confidence,
                timeframe=timeframe,
                verbose=True
            )

            if high_conf:
                sent_signals = save_and_notify_signals(high_conf, min_confidence, timeframe, sent_signals)

            # Wait for next scan
            next_scan = datetime.now().timestamp() + (scan_interval_minutes * 60)
            print(f"\n⏳ Next scan in {scan_interval_minutes} minutes...")
            print(f"   Next scan at: {datetime.fromtimestamp(next_scan).strftime('%Y-%m-%d %H:%M:%S')}")

            time.sleep(scan_interval_minutes * 60)

    except KeyboardInterrupt:
        print("\n\n🛑 Stopping scanner...")
        print(f"✅ Completed {scan_count} scans")
        print("="*80)


if __name__ == "__main__":
    import sys

    # Parse command line arguments
    min_conf = 50
    run_continuous = True

    if len(sys.argv) > 1:
        if sys.argv[1] == '--once':
            run_continuous = False
        else:
            try:
                min_conf = int(sys.argv[1])
            except:
                pass

    if run_continuous:
        continuous_scan(
            min_confidence=min_conf,
            timeframe=TIMEFRAME,
            scan_interval_minutes=SCAN_INTERVAL_MINUTES
        )
    else:
        # Single scan mode
        high_conf, watch_list = scan_for_signals(
            min_confidence=min_conf,
            timeframe=TIMEFRAME,
            verbose=True
        )
        if high_conf:
            save_and_notify_signals(high_conf, min_conf, TIMEFRAME, set())
