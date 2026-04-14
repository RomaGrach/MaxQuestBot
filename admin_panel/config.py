from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values


def _as_bool(raw_value: str | None, default: bool = False) -> bool:
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(slots=True)
class AdminPanelSettings:
    host: str = "127.0.0.1"
    port: int = 8081
    db_path: str = ".local/admin_panel.sqlite3"
    secret_key: str = "dev-only-secret-change-me"
    session_cookie_name: str = "maxquest_admin_session"
    session_max_age: int = 60 * 60 * 12
    session_cookie_secure: bool = False
    bootstrap_admin_username: str | None = None
    bootstrap_admin_password: str | None = None

    @classmethod
    def from_env(cls) -> "AdminPanelSettings":
        values = {
            **dotenv_values(),
            **dotenv_values(Path(".env.local")),
            **os.environ,
        }
        return cls(
            host=str(values.get("ADMIN_PANEL_HOST", "127.0.0.1")).strip(),
            port=int(str(values.get("ADMIN_PANEL_PORT", "8081"))),
            db_path=str(values.get("ADMIN_PANEL_DB_PATH", ".local/admin_panel.sqlite3")).strip(),
            secret_key=str(values.get("ADMIN_PANEL_SECRET_KEY", "dev-only-secret-change-me")).strip(),
            session_cookie_name=str(values.get("ADMIN_PANEL_SESSION_COOKIE_NAME", "maxquest_admin_session")).strip(),
            session_max_age=int(str(values.get("ADMIN_PANEL_SESSION_MAX_AGE", 60 * 60 * 12))),
            session_cookie_secure=_as_bool(
                str(values["ADMIN_PANEL_COOKIE_SECURE"])
                if values.get("ADMIN_PANEL_COOKIE_SECURE") is not None
                else None,
                False,
            ),
            bootstrap_admin_username=(
                str(values["ADMIN_PANEL_BOOTSTRAP_USERNAME"]).strip()
                if values.get("ADMIN_PANEL_BOOTSTRAP_USERNAME")
                else None
            ),
            bootstrap_admin_password=(
                str(values["ADMIN_PANEL_BOOTSTRAP_PASSWORD"]).strip()
                if values.get("ADMIN_PANEL_BOOTSTRAP_PASSWORD")
                else None
            ),
        )

    def validate(self) -> None:
        if not self.secret_key:
            raise ValueError("ADMIN_PANEL_SECRET_KEY must not be empty.")
        if self.secret_key == "dev-only-secret-change-me" and self.session_cookie_secure:
            raise ValueError(
                "ADMIN_PANEL_SECRET_KEY must be changed before using secure cookies."
            )
        if (self.bootstrap_admin_username is None) != (
            self.bootstrap_admin_password is None
        ):
            raise ValueError(
                "Set both ADMIN_PANEL_BOOTSTRAP_USERNAME and ADMIN_PANEL_BOOTSTRAP_PASSWORD, or neither."
            )

    @property
    def resolved_db_path(self) -> Path:
        return Path(self.db_path).expanduser().resolve()
