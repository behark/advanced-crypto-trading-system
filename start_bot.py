#!/usr/bin/env python3
"""
Start the Trading Bot with Telegram notifications (env-based credentials)
- TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in environment
"""

import os
import sys

from trading_bot import TradingBot

# Read Telegram credentials from environment
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("❌ Missing Telegram credentials: set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")
    sys.exit(1)

# Initialize bot with 15 crypto pairs (paper trading enabled)
bot = TradingBot(
    exchange_name='binance',
    account_balance=10000,
    dry_run=True,  # Paper trading mode
    symbols=[
        'BTC/USDT:USDT',
        'ETH/USDT:USDT',
        'DOGE/USDT:USDT',
        'SOL/USDT:USDT',
        'XRP/USDT:USDT',
        'ADA/USDT:USDT',
        'LINK/USDT:USDT',
        'AVAX/USDT:USDT',
        'MATIC/USDT:USDT',
        'UNI/USDT:USDT',
        'ATOM/USDT:USDT',
        'ARB/USDT:USDT',
        'OP/USDT:USDT',
        'LTC/USDT:USDT',
        'LAB/USDT:USDT'
    ],
    telegram_bot_token=TELEGRAM_BOT_TOKEN,
    telegram_chat_id=TELEGRAM_CHAT_ID,
)

# Print status
bot.print_status()

# Run continuous monitoring (checks every 1 minute)
print("\n" + "="*80)
print("Starting monitoring loop - Press Ctrl+C to stop")
print("="*80)

bot.run_loop(interval_minutes=1)
