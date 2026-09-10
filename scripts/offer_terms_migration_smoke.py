import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PREVIOUS_REVISION = "20260910_1600_telegram_outbox"
CURRENT_REVISION = "20260910_1930_offer_terms"
OFFER_TERM_COLUMNS = {
    "included_services",
    "possible_surcharges",
    "service_window",
    "estimate_status",
}


def run_alembic(env: dict[str, str], *arguments: str) -> None:
    subprocess.run(
        [sys.executable, "-m", "alembic", *arguments],
        cwd=ROOT,
        env=env,
        check=True,
    )


def offer_columns(database: Path) -> set[str]:
    with sqlite3.connect(database) as connection:
        return {
            row[1]
            for row in connection.execute("PRAGMA table_info(job_offer)")
        }


def main() -> None:
    with tempfile.TemporaryDirectory(
        prefix="cargopt-offer-terms-migration-"
    ) as temporary:
        database = Path(temporary) / "migration.db"
        env = os.environ.copy()
        env["DATABASE_URL"] = f"sqlite+aiosqlite:///{database}"
        env["BOT_TOKEN"] = "migration-smoke"

        run_alembic(env, "upgrade", "head")
        assert OFFER_TERM_COLUMNS <= offer_columns(database)
        with sqlite3.connect(database) as connection:
            revision = connection.execute(
                "SELECT version_num FROM alembic_version"
            ).fetchone()[0]
            assert revision == CURRENT_REVISION

        run_alembic(env, "downgrade", PREVIOUS_REVISION)
        assert not (OFFER_TERM_COLUMNS & offer_columns(database))

    print("OFFER_TERMS_MIGRATION_SMOKE_OK")


if __name__ == "__main__":
    main()
