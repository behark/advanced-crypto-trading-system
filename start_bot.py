#!/usr/bin/env python3
"""
Start the Trading Bot with Telegram notifications (env-based credentials)
- TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID loaded from .env file
"""

import os
import sys
from pathlib import Path

from trading_bot import TradingBot

# Load .env file
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Read Telegram credentials from environment
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("❌ Missing Telegram credentials: set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")
    sys.exit(1)

# Initialize bot with pairs from config_harmonic.yaml (paper trading enabled)
bot = TradingBot(
    exchange_name='binance',
    account_balance=10000,
    dry_run=True,  # Paper trading mode
    symbols=[
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
    ],
    telegram_bot_token=TELEGRAM_BOT_TOKEN,
    telegram_chat_id=TELEGRAM_CHAT_ID,
    discord_webhook_url=os.getenv("DISCORD_WEBHOOK_URL"),
    slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL"),
    country=os.getenv("TRADING_COUNTRY", "Global"),
)

# Print status
bot.print_status()

# Run continuous monitoring (checks every 60 minutes = 1 hour)
print("\n" + "="*80)
print("Starting monitoring loop - Press Ctrl+C to stop")
print("="*80)

bot.run_loop(interval_minutes=60)
