import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PREVIOUS_REVISION = "20260910_1500_web_idempotency"
CURRENT_REVISION = "20260910_1600_telegram_outbox"


def run_alembic(env: dict[str, str], *arguments: str) -> None:
    subprocess.run(
        [sys.executable, "-m", "alembic", *arguments],
        cwd=ROOT,
        env=env,
        check=True,
    )


def insert_job(connection: sqlite3.Connection) -> int:
    cursor = connection.execute(
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
            updated_at
        ) VALUES ('ready_for_matching', 0, 0, 0, 0, 0, 0, ?, ?)
        """,
        ("2026-09-10T00:00:00+00:00", "2026-09-10T00:00:00+00:00"),
    )
    return int(cursor.lastrowid)


def insert_notification(
    connection: sqlite3.Connection,
    *,
    job_id: int,
    dedupe_key: str,
) -> None:
    connection.execute(
        """
        INSERT INTO telegram_notification_outbox (
            job_id,
            offer_id,
            notification_type,
            recipient_chat_id,
            dedupe_key,
            delivery_status,
            attempt_count,
            created_at,
            updated_at
        ) VALUES (?, NULL, 'manual_review', 123456, ?, 'pending', 0, ?, ?)
        """,
        (
            job_id,
            dedupe_key,
            "2026-09-10T00:00:00+00:00",
            "2026-09-10T00:00:00+00:00",
        ),
    )


def main() -> None:
    with tempfile.TemporaryDirectory(
        prefix="cargopt-telegram-outbox-migration-"
    ) as temporary:
        database = Path(temporary) / "migration.db"
        env = os.environ.copy()
        env["DATABASE_URL"] = f"sqlite+aiosqlite:///{database}"
        env["BOT_TOKEN"] = "migration-smoke"

        run_alembic(env, "upgrade", CURRENT_REVISION)

        connection = sqlite3.connect(database)
        try:
            columns = {
                row[1]
                for row in connection.execute(
                    "PRAGMA table_info(telegram_notification_outbox)"
                )
            }
            assert {
                "job_id",
                "offer_id",
                "notification_type",
                "recipient_chat_id",
                "dedupe_key",
                "delivery_status",
                "attempt_count",
                "next_attempt_at",
                "last_attempt_at",
                "sent_at",
                "provider_chat_id",
                "provider_message_id",
                "last_error",
            } <= columns
            indexes = {
                row[1]: row[2]
                for row in connection.execute(
                    "PRAGMA index_list(telegram_notification_outbox)"
                )
            }
            assert indexes["ux_telegram_notification_dedupe_key"] == 1

            job_id = insert_job(connection)
            insert_notification(
                connection,
                job_id=job_id,
                dedupe_key="manual-review:1",
            )
            try:
                insert_notification(
                    connection,
                    job_id=job_id,
                    dedupe_key="manual-review:1",
                )
            except sqlite3.IntegrityError:
                pass
            else:
                raise AssertionError("duplicate notification key was accepted")
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
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            assert "telegram_notification_outbox" not in tables
        finally:
            connection.close()

    print("TELEGRAM_NOTIFICATION_OUTBOX_MIGRATION_SMOKE_OK")


if __name__ == "__main__":
    main()
