#!/bin/bash
# Tracker for Bot 9: binance_crypto.py
cd /home/behar/tradingview-custom-screener
python3 signal_tracker.py \
    signals_log_bot9.json \
    tracker_results_bot9.json \
    "8485892407:AAFVHtNqiYM_HzJpgKeqjDYKmECYFHoWzdc" \
    "1507876704" \
    "Bot9-BinanceCrypto" \
    "binance" > tracker_bot9.log 2>&1 &
echo $! > tracker_bot9.pid
echo "Tracker started for Bot 9 (PID: $(cat tracker_bot9.pid))"
