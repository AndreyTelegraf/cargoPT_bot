import os
import subprocess
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    service = (
        PROJECT_ROOT / "deploy/systemd/cargopt_telegram_dispatch.service"
    ).read_text(encoding="utf-8")
    timer = (
        PROJECT_ROOT / "deploy/systemd/cargopt_telegram_dispatch.timer"
    ).read_text(encoding="utf-8")
    assert "EnvironmentFile=/etc/cargopt_bot/cargopt_bot.env" in service
    assert "-m scripts.dispatch_telegram_notifications" in service
    assert "ReadWritePaths=/opt/bots/cargoPT_bot/data" in service
    assert "NoNewPrivileges=yes" in service
    assert "OnUnitActiveSec=1min" in timer
    assert "Persistent=true" in timer

    with tempfile.TemporaryDirectory(
        prefix="cargopt-telegram-dispatch-entrypoint-"
    ) as temporary:
        database = Path(temporary) / "entrypoint.db"
        environment = os.environ.copy()
        environment.update(
            {
                "BOT_TOKEN": "123456:TESTTOKEN",
                "DATABASE_URL": f"sqlite+aiosqlite:///{database}",
                "ENVIRONMENT": "telegram-dispatch-entrypoint-smoke",
            }
        )
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=PROJECT_ROOT,
            env=environment,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        result = subprocess.run(
            [sys.executable, "-m", "scripts.dispatch_telegram_notifications"],
            cwd=PROJECT_ROOT,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        assert "TELEGRAM_DISPATCH_PROCESSED=0" in result.stdout

    print("TELEGRAM_NOTIFICATION_DISPATCH_ENTRYPOINT_SMOKE_OK")


if __name__ == "__main__":
    main()
