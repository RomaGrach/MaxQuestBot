from __future__ import annotations

import uvicorn

from admin_panel.app import create_app
from admin_panel.config import AdminPanelSettings


def main() -> None:
    settings = AdminPanelSettings.from_env()
    settings.validate()
    uvicorn.run(
        create_app(settings),
        host=settings.host,
        port=settings.port,
        proxy_headers=True,
    )


if __name__ == "__main__":
    main()
