#!/usr/bin/env python3
"""
Notification helpers for multi-channel alerts.
Supports Telegram, Discord, and Slack webhooks.
"""

import requests
from typing import Dict, Optional


class NotificationManager:
    """Send notifications across multiple channels."""

    def __init__(
        self,
        telegram_bot_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        discord_webhook_url: Optional[str] = None,
        slack_webhook_url: Optional[str] = None,
    ) -> None:
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id
        self.discord_webhook_url = discord_webhook_url
        self.slack_webhook_url = slack_webhook_url

        self.telegram_enabled = bool(self.telegram_bot_token and self.telegram_chat_id)
        self.discord_enabled = bool(self.discord_webhook_url)
        self.slack_enabled = bool(self.slack_webhook_url)

    def enabled_channels(self) -> Dict[str, bool]:
        return {
            "telegram": self.telegram_enabled,
            "discord": self.discord_enabled,
            "slack": self.slack_enabled,
        }

    def send(self, message: str) -> Dict[str, bool]:
        results = {}

        if self.telegram_enabled:
            results["telegram"] = self._send_telegram(message)

        if self.discord_enabled:
            results["discord"] = self._send_discord(message)

        if self.slack_enabled:
            results["slack"] = self._send_slack(message)

        return results

    def _send_telegram(self, message: str) -> bool:
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            data = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML",
            }
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
        except Exception as exc:
            print(f"❌ Telegram error: {exc}")
            return False

    def _send_discord(self, message: str) -> bool:
        try:
            data = {"content": message}
            response = requests.post(self.discord_webhook_url, json=data, timeout=10)
            return response.status_code in {200, 204}
        except Exception as exc:
            print(f"❌ Discord error: {exc}")
            return False

    def _send_slack(self, message: str) -> bool:
        try:
            data = {"text": message}
            response = requests.post(self.slack_webhook_url, json=data, timeout=10)
            return response.status_code == 200
        except Exception as exc:
            print(f"❌ Slack error: {exc}")
            return False
