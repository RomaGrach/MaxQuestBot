from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


def _as_bool(raw_value: str | None, default: bool = False) -> bool:
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(slots=True)
class Settings:
    max_bot_token: str
    run_mode: str = "polling"
    host: str = "0.0.0.0"
    port: int = 8080
    webhook_path: str = "/webhook"
    webhook_secret: str | None = None
    log_level: str = "INFO"
    require_phone: bool = False
    backend_mode: str = "sqlite"
    db_path: str = ".local/admin_panel.sqlite3"

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            max_bot_token=os.getenv("MAX_BOT_TOKEN", "").strip(),
            run_mode=os.getenv("BOT_RUN_MODE", "polling").strip().lower(),
            host=os.getenv("BOT_HOST", "0.0.0.0").strip(),
            port=int(os.getenv("BOT_PORT", "8080")),
            webhook_path=os.getenv("BOT_WEBHOOK_PATH", "/webhook").strip(),
            webhook_secret=os.getenv("BOT_WEBHOOK_SECRET") or None,
            log_level=os.getenv("BOT_LOG_LEVEL", "INFO").strip().upper(),
            require_phone=_as_bool(os.getenv("BOT_REQUIRE_PHONE"), False),
            backend_mode=os.getenv("BOT_BACKEND", "sqlite").strip().lower(),
            db_path=(
                os.getenv("BOT_DB_PATH")
                or os.getenv("ADMIN_PANEL_DB_PATH")
                or ".local/admin_panel.sqlite3"
            ).strip(),
        )

    def validate(self) -> None:
        if not self.max_bot_token:
            raise ValueError(
                "MAX_BOT_TOKEN is empty. Set the bot token in .env or environment."
            )
        if self.run_mode not in {"polling", "webhook"}:
            raise ValueError("BOT_RUN_MODE must be either 'polling' or 'webhook'.")
        if self.backend_mode not in {"sqlite", "memory"}:
            raise ValueError("BOT_BACKEND must be either 'sqlite' or 'memory'.")
        if not self.webhook_path.startswith("/"):
            raise ValueError("BOT_WEBHOOK_PATH must start with '/'.")
