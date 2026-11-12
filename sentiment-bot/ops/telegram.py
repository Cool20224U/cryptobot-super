"""Authenticated control plane. Commands allowlisted; every command audited.
Keys from env only. /stop is a first-class, rehearsed operation."""
from __future__ import annotations

import logging
import os

log = logging.getLogger("ops.telegram")

ALLOWED_COMMANDS = {"/stop", "/status", "/flatten", "/help"}


class TelegramControl:
    def __init__(self, bus, allowed_chat_ids: list) -> None:
        self.bus = bus
        self.allowed = {int(c) for c in allowed_chat_ids}
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "")

    def is_authorized(self, chat_id: int) -> bool:
        return int(chat_id) in self.allowed

    def handle(self, chat_id: int, text: str) -> str:
        if not self.is_authorized(chat_id):
            log.warning("unauthorized command attempt chat=%s", chat_id)
            return "unauthorized"
        cmd = text.strip().split()[0]
        if cmd not in ALLOWED_COMMANDS:
            return "unknown command"
        log.info("command=%s chat=%s", cmd, chat_id)
        if cmd == "/stop" or cmd == "/flatten":
            self.bus.publish("control", "flatten")
        elif cmd == "/status":
            self.bus.publish("control", "status")
        return cmd
