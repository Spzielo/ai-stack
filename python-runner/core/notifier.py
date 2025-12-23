"""
Notification Hub — Slack Integration
core/notifier.py

Usage:
    from core.notifier import notifier
    notifier.send("Titre", "Message")
    notifier.warning("Alerte", "Attention requise")
"""

import os
import logging
import json
from enum import IntEnum
from dataclasses import dataclass
from typing import Optional, Dict, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


logger = logging.getLogger(__name__)


class Priority(IntEnum):
    """Slack priority levels (mapped to formatting/emoji)."""
    LOWEST = -2      # Pas de notif visible (ou log seulement)
    LOW = -1         # Discret
    NORMAL = 0       # Standard
    HIGH = 1         # Important (Warning)
    CRITICAL = 2     # Urgent (Error/Mention)


class Notifier:
    """Client Slack via Incoming Webhook (Dual Channel)."""

    def __init__(self):
        self._session = self._create_session()
        # Load both webhooks
        self._webhook_log = os.getenv("SLACK_WEBHOOK_LOG")
        self._webhook_alert = os.getenv("SLACK_WEBHOOK_ALERT")
        
        # Fallback for backward compatibility (during migration)
        self._webhook_default = os.getenv("SLACK_WEBHOOK_URL")

        if not self._webhook_log and not self._webhook_alert and not self._webhook_default:
            logger.warning("No SLACK_WEBHOOK_* configured. Notifications disabled.")

    def _create_session(self) -> requests.Session:
        """Crée une session HTTP avec retry automatique."""
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        session.mount("https://", HTTPAdapter(max_retries=retry))
        return session

    def is_configured(self) -> bool:
        return bool(self._webhook_log or self._webhook_alert or self._webhook_default)

    def _get_webhook_for_priority(self, priority: Priority) -> Optional[str]:
        """Routes message to correct webhook based on priority."""
        
        # High priority -> Alert Channel
        if priority >= Priority.HIGH:
            return self._webhook_alert or self._webhook_default
            
        # Normal/Low priority -> Log Channel
        return self._webhook_log or self._webhook_default

    def _format_payload(self, title: str, message: str, priority: Priority) -> Dict[str, Any]:
        """Formate le message en JSON Slack."""
        
        # Emoji prefixes based on priority
        emoji = "ℹ️"
        
        if priority == Priority.LOW or priority == Priority.LOWEST:
            emoji = "🪵"
        elif priority == Priority.HIGH:
            emoji = "⚠️"
        elif priority == Priority.CRITICAL:
            emoji = "🚨"

        # Blocks layout for nicer formatting
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            },
            {
                "type": "divider"
            }
        ]

        return {
            "blocks": blocks,
            "text": f"{emoji} {title}: {message}"
        }

    def send(
        self,
        title: str,
        message: str,
        priority: Priority = Priority.NORMAL,
    ) -> bool:
        """Envoie une notification Slack."""
        webhook_url = self._get_webhook_for_priority(priority)
        
        if not webhook_url:
            logger.debug(f"Notification skipped (no webhook for priority {priority}): {title}")
            return False

        payload = self._format_payload(title, message, priority)

        try:
            response = self._session.post(
                webhook_url,
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            logger.info(f"Notification Slack envoyée ({priority.name}): {title}")
            return True

        except requests.RequestException as e:
            logger.error(f"Échec notification Slack: {e}")
            return False

    def info(self, title: str, message: str) -> bool:
        return self.send(title, message, Priority.NORMAL)

    def warning(self, title: str, message: str) -> bool:
        return self.send(title, message, Priority.HIGH)

    def critical(self, title: str, message: str) -> bool:
        return self.send(title, message, Priority.CRITICAL)


# Singleton
notifier = Notifier()
