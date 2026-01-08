#!/bin/bash
# Continuous Binance Crypto Analyzer
# Runs analysis on multiple pairs every 10 minutes

SYMBOLS=("BTC/USDT" "ETH/USDT" "MINA/USDT" "APR/USDT" "LAB/USDT")
TIMEFRAME="15m"

echo "🔄 Binance Continuous Analyzer Started"
echo "Pairs: ${SYMBOLS[@]}"
echo "Timeframe: $TIMEFRAME"
echo "Interval: 10 minutes"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

while true; do
    echo ""
    echo "📊 Scan: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    for symbol in "${SYMBOLS[@]}"; do
        echo ""
        echo "Analyzing: $symbol"
        python3 binance_crypto.py "$symbol" "$TIMEFRAME" 2>&1 | grep -E "Signal|LONG|SHORT|Entry|Stop|Price"
    done

    echo ""
    echo "⏳ Waiting 10 minutes until next scan..."
    sleep 600  # 10 minutes
done
