from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import sqlite3
import sys
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.outcome_metrics import build_report


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE job (
            id INTEGER PRIMARY KEY,
            source TEXT,
            source_locale TEXT,
            utm_source TEXT,
            status TEXT NOT NULL,
            requested_date TEXT,
            client_telegram_user_id INTEGER,
            customer_email TEXT,
            client_phone TEXT,
            client_whatsapp TEXT,
            comment TEXT,
            short_lead_time_filtered INTEGER NOT NULL DEFAULT 0,
            assigned_at TEXT,
            completed_at TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE job_address (
            id INTEGER PRIMARY KEY,
            job_id INTEGER NOT NULL,
            kind TEXT NOT NULL
        );
        CREATE TABLE job_item (
            id INTEGER PRIMARY KEY,
            job_id INTEGER NOT NULL
        );
        CREATE TABLE job_offer (
            id INTEGER PRIMARY KEY,
            job_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            price_cents INTEGER,
            responded_at TEXT
        );
        CREATE TABLE telegram_notification_outbox (
            id INTEGER PRIMARY KEY,
            job_id INTEGER NOT NULL,
            notification_type TEXT NOT NULL,
            delivery_status TEXT NOT NULL
        );
        CREATE TABLE acquisition_event_daily (
            id INTEGER PRIMARY KEY,
            event_date TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_count INTEGER NOT NULL
        );
        """
    )


def _insert_quality_job(
    connection: sqlite3.Connection,
    *,
    job_id: int,
    source: str,
    status: str,
    short_lead: bool = False,
    assigned_at: str | None = None,
) -> None:
    connection.execute(
        """
        INSERT INTO job (
            id, source, source_locale, utm_source, status, requested_date,
            customer_email, comment, short_lead_time_filtered, assigned_at,
            created_at
        ) VALUES (?, ?, 'pt', 'owned_test', ?, '2026-09-20 10:00:00+00:00',
                  'client@example.test', 'boxes', ?, ?, '2026-09-09 10:00:00+00:00')
        """,
        (job_id, source, status, int(short_lead), assigned_at),
    )
    connection.executemany(
        "INSERT INTO job_address (job_id, kind) VALUES (?, ?)",
        ((job_id, "pickup"), (job_id, "dropoff")),
    )


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="cargopt-outcome-metrics-") as tmp:
        database = Path(tmp) / "metrics.sqlite3"
        connection = sqlite3.connect(database)
        _create_schema(connection)
        _insert_quality_job(
            connection,
            job_id=1,
            source="web_form",
            status="assigned",
            assigned_at="2026-09-09 13:00:00+00:00",
        )
        _insert_quality_job(
            connection,
            job_id=2,
            source="web_form",
            status="manual_review_required",
            short_lead=True,
        )
        _insert_quality_job(
            connection,
            job_id=3,
            source="synthetic_test",
            status="completed",
            assigned_at="2026-09-09 12:00:00+00:00",
        )
        connection.execute(
            """
            INSERT INTO job (id, source, status, created_at)
            VALUES (4, 'web_form', 'draft', '2026-09-09 10:00:00+00:00')
            """
        )
        connection.executemany(
            """
            INSERT INTO job_offer (job_id, status, price_cents, responded_at)
            VALUES (?, 'accepted', ?, ?)
            """,
            (
                (1, 10000, "2026-09-09 11:00:00+00:00"),
                (1, 12000, "2026-09-09 12:00:00+00:00"),
                (1, None, "2026-09-09 10:30:00+00:00"),
            ),
        )
        connection.execute(
            """
            INSERT INTO telegram_notification_outbox
                (job_id, notification_type, delivery_status)
            VALUES (1, 'carrier_offer', 'sent')
            """
        )
        connection.executemany(
            """
            INSERT INTO acquisition_event_daily
                (event_date, event_type, event_count)
            VALUES ('2026-09-09', ?, ?)
            """,
            (("landing_view", 10), ("submit_success", 2)),
        )
        connection.commit()
        connection.close()

        report = build_report(
            database,
            days=7,
            now=datetime(2026, 9, 10, 12, 0, tzinfo=UTC),
        )
        requests = report["requests"]
        assert requests["confirmed_unique"] == 2
        assert requests["quality_unique"] == 2
        assert requests["manual_review"] == 1
        assert requests["manual_short_lead"] == 1
        assert requests["with_created_offers"] == 1
        assert requests["with_at_least_one_price"] == 1
        assert requests["with_at_least_two_prices"] == 1
        assert requests["selected"] == 1
        assert requests["assignment_confirmed"] == 1
        assert requests["completed"] == 0
        assert report["time_to_first_price_seconds"]["median"] == 3600
        assert report["carrier_offer_delivery"]["represented_jobs"] == 1
        assert report["carrier_offer_delivery"]["sent_jobs"] == 1
        assert report["browser_events"] == {"landing_view": 10, "submit_success": 2}
        assert len(report["attribution"]) == 1
        assert report["attribution"][0]["quality_requests"] == 2

    print("OUTCOME_METRICS_SMOKE_OK")


if __name__ == "__main__":
    main()
