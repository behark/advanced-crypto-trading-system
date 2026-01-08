#!/bin/bash
# Tracker for Bot9_BinanceCrypto

BOT_DIR="/home/behar/tradingview-custom-screener"
BOT_NAME="Bot9_BinanceCrypto"
TELEGRAM_TOKEN="YOUR_TOKEN_HERE"
TELEGRAM_CHAT_ID="1507876704"
EXCHANGE="binance"

cd "$BOT_DIR"

# Kill existing tracker if running
pkill -f "signal_tracker.py.*${BOT_NAME}" || true
sleep 2

# Start tracker in background
nohup python3 signal_tracker.py \
    "$BOT_DIR/signals_log.json" \
    "$BOT_DIR/tracker_results.json" \
    "$TELEGRAM_TOKEN" \
    "$TELEGRAM_CHAT_ID" \
    "$BOT_NAME" \
    "$EXCHANGE" > "$BOT_DIR/tracker.log" 2>&1 &

TRACKER_PID=$!

echo "✅ Tracker started for $BOT_NAME"
echo "PID: $TRACKER_PID"
echo "Log: tail -f $BOT_DIR/tracker.log"
echo ""
echo "To stop: pkill -f 'signal_tracker.py.*${BOT_NAME}'"
