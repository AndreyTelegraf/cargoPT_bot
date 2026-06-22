import os
import shutil
import sqlite3
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "cargopt_dev.db"

EXPECTED_TABLES = {
    "alembic_version",
    "admin_invite_token",
    "carrier_company",
    "carrier_vehicle",
    "job",
    "job_address",
    "job_item",
}


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def reset_db() -> None:
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    DATA_DIR.mkdir(exist_ok=True)


def assert_tables() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"DB file missing: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
        }
    finally:
        conn.close()

    missing = EXPECTED_TABLES - tables
    extra = tables - EXPECTED_TABLES

    if missing:
        raise SystemExit(f"Missing tables: {sorted(missing)}")

    if extra:
        raise SystemExit(f"Unexpected tables: {sorted(extra)}")


def main() -> None:
    os.environ["BOT_TOKEN"] = "db-smoke-token"
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"
    os.environ["ENVIRONMENT"] = "db-smoke"
    os.environ["LOG_LEVEL"] = "INFO"

    reset_db()

    run([".venv/bin/alembic", "upgrade", "head"])
    assert_tables()

    run([".venv/bin/alembic", "current"])

    run([".venv/bin/alembic", "downgrade", "base"])
    run([".venv/bin/alembic", "upgrade", "head"])
    assert_tables()

    shutil.rmtree(DATA_DIR)

    print("DB_SMOKE_OK")


if __name__ == "__main__":
    main()
