import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PREVIOUS_REVISION = "20260903_1200_short_lead_filter"
CURRENT_REVISION = "20260910_1500_web_idempotency"


def run_alembic(env: dict[str, str], *arguments: str) -> None:
    subprocess.run(
        [sys.executable, "-m", "alembic", *arguments],
        cwd=ROOT,
        env=env,
        check=True,
    )


def insert_job(
    connection: sqlite3.Connection,
    *,
    key: str | None,
    fingerprint: str | None,
) -> None:
    connection.execute(
        """
        INSERT INTO job (
            status,
            needs_assembly,
            needs_packing,
            needs_tail_lift,
            needs_crane,
            needs_mobile_lift,
            short_lead_time_filtered,
            created_at,
            updated_at,
            web_idempotency_key,
            web_request_fingerprint
        ) VALUES (?, 0, 0, 0, 0, 0, 0, ?, ?, ?, ?)
        """,
        (
            "ready_for_matching",
            "2026-09-10T00:00:00+00:00",
            "2026-09-10T00:00:00+00:00",
            key,
            fingerprint,
        ),
    )


def main() -> None:
    with tempfile.TemporaryDirectory(
        prefix="cargopt-web-idempotency-migration-"
    ) as temporary:
        database = Path(temporary) / "migration.db"
        env = os.environ.copy()
        env["DATABASE_URL"] = f"sqlite+aiosqlite:///{database}"
        env["BOT_TOKEN"] = "migration-smoke"

        run_alembic(env, "upgrade", "head")

        connection = sqlite3.connect(database)
        try:
            columns = {
                row[1]
                for row in connection.execute("PRAGMA table_info(job)")
            }
            assert {
                "web_idempotency_key",
                "web_request_fingerprint",
            } <= columns

            indexes = {
                row[1]: row[2]
                for row in connection.execute("PRAGMA index_list(job)")
            }
            assert indexes["ux_job_web_idempotency_key"] == 1

            fingerprint = "a" * 64
            insert_job(
                connection,
                key="same-web-submit",
                fingerprint=fingerprint,
            )
            try:
                insert_job(
                    connection,
                    key="same-web-submit",
                    fingerprint=fingerprint,
                )
            except sqlite3.IntegrityError:
                pass
            else:
                raise AssertionError("duplicate idempotency key was accepted")

            insert_job(connection, key=None, fingerprint=None)
            insert_job(connection, key=None, fingerprint=None)
            connection.rollback()

            revision = connection.execute(
                "SELECT version_num FROM alembic_version"
            ).fetchone()[0]
            assert revision == CURRENT_REVISION
        finally:
            connection.close()

        run_alembic(env, "downgrade", PREVIOUS_REVISION)

        connection = sqlite3.connect(database)
        try:
            columns = {
                row[1]
                for row in connection.execute("PRAGMA table_info(job)")
            }
            assert "web_idempotency_key" not in columns
            assert "web_request_fingerprint" not in columns
            indexes = {
                row[1]
                for row in connection.execute("PRAGMA index_list(job)")
            }
            assert "ux_job_web_idempotency_key" not in indexes
        finally:
            connection.close()

    print("WEB_IDEMPOTENCY_MIGRATION_SMOKE_OK")


if __name__ == "__main__":
    main()
