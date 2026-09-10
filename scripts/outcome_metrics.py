from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import sqlite3
from typing import Any


DEFAULT_DATABASE = Path("/opt/bots/cargoPT_bot/data/cargopt_prod.db")
EXCLUDED_LIFECYCLE_STATUSES = ("draft", "draft_expired")


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)


def _nearest_rank(values: list[float], percentile: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, int(len(ordered) * percentile + 0.999999))
    return round(ordered[min(rank, len(ordered)) - 1])


def _label(value: str | None) -> str:
    normalized = (value or "").strip()
    return normalized if normalized else "(unspecified)"


def _quality_job_rows(
    connection: sqlite3.Connection,
    *,
    cutoff: datetime,
    include_synthetic: bool,
) -> list[sqlite3.Row]:
    source_filter = "" if include_synthetic else "AND lower(coalesce(j.source, '')) NOT LIKE 'synthetic%'"
    return connection.execute(
        f"""
        SELECT j.*
        FROM job AS j
        WHERE j.created_at >= ?
          AND j.status NOT IN (?, ?)
          {source_filter}
          AND j.requested_date IS NOT NULL
          AND (
              j.client_telegram_user_id IS NOT NULL
              OR trim(coalesce(j.customer_email, '')) != ''
              OR trim(coalesce(j.client_phone, '')) != ''
              OR trim(coalesce(j.client_whatsapp, '')) != ''
          )
          AND (
              trim(coalesce(j.comment, '')) != ''
              OR EXISTS (SELECT 1 FROM job_item AS ji WHERE ji.job_id = j.id)
          )
          AND EXISTS (
              SELECT 1 FROM job_address AS ja
              WHERE ja.job_id = j.id AND ja.kind = 'pickup'
          )
          AND EXISTS (
              SELECT 1 FROM job_address AS ja
              WHERE ja.job_id = j.id AND ja.kind = 'dropoff'
          )
        ORDER BY j.id
        """,
        (
            cutoff.isoformat(sep=" "),
            EXCLUDED_LIFECYCLE_STATUSES[0],
            EXCLUDED_LIFECYCLE_STATUSES[1],
        ),
    ).fetchall()


def _event_counters(
    connection: sqlite3.Connection,
    *,
    cutoff: datetime,
) -> dict[str, int]:
    rows = connection.execute(
        """
        SELECT event_type, SUM(event_count) AS event_count
        FROM acquisition_event_daily
        WHERE event_date >= ?
        GROUP BY event_type
        ORDER BY event_type
        """,
        (cutoff.date().isoformat(),),
    ).fetchall()
    return {row["event_type"]: int(row["event_count"]) for row in rows}


def _source_breakdown(
    connection: sqlite3.Connection,
    *,
    quality_ids: list[int],
) -> list[dict[str, Any]]:
    if not quality_ids:
        return []
    placeholders = ",".join("?" for _ in quality_ids)
    rows = connection.execute(
        f"""
        SELECT
            coalesce(nullif(trim(j.source), ''), '(unspecified)') AS source,
            coalesce(nullif(trim(j.source_locale), ''), '(unspecified)') AS locale,
            coalesce(nullif(trim(j.utm_source), ''), '(unspecified)') AS utm_source,
            COUNT(DISTINCT j.id) AS quality_requests,
            COUNT(DISTINCT CASE WHEN j.status = 'manual_review_required' THEN j.id END) AS manual_review,
            COUNT(DISTINCT CASE WHEN jo.price_cents IS NOT NULL THEN j.id END) AS with_price,
            COUNT(DISTINCT CASE
                WHEN j.assigned_at IS NOT NULL
                  OR j.status IN ('assigned_pending_confirmation', 'assigned', 'in_progress', 'completed')
                THEN j.id END
            ) AS selected,
            COUNT(DISTINCT CASE
                WHEN j.completed_at IS NOT NULL OR j.status = 'completed'
                THEN j.id END
            ) AS completed
        FROM job AS j
        LEFT JOIN job_offer AS jo ON jo.job_id = j.id
        WHERE j.id IN ({placeholders})
        GROUP BY source, locale, utm_source
        ORDER BY quality_requests DESC, source, locale, utm_source
        """,
        quality_ids,
    ).fetchall()
    return [dict(row) for row in rows]


def build_report(
    database: Path,
    *,
    days: int,
    now: datetime | None = None,
    include_synthetic: bool = False,
) -> dict[str, Any]:
    checked_at = now or datetime.now(UTC)
    if checked_at.tzinfo is None:
        checked_at = checked_at.replace(tzinfo=UTC)
    checked_at = checked_at.astimezone(UTC)
    cutoff = checked_at - timedelta(days=days)

    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        quick_check = connection.execute("PRAGMA quick_check").fetchone()[0]
        if quick_check != "ok":
            raise RuntimeError(f"database quick_check failed: {quick_check}")

        confirmed_params: list[Any] = [
            cutoff.isoformat(sep=" "),
            *EXCLUDED_LIFECYCLE_STATUSES,
        ]
        confirmed_source_filter = ""
        if not include_synthetic:
            confirmed_source_filter = "AND lower(coalesce(source, '')) NOT LIKE 'synthetic%'"
        confirmed_requests = int(
            connection.execute(
                f"""
                SELECT COUNT(*)
                FROM job
                WHERE created_at >= ?
                  AND status NOT IN (?, ?)
                  {confirmed_source_filter}
                """,
                confirmed_params,
            ).fetchone()[0]
        )

        quality_rows = _quality_job_rows(
            connection,
            cutoff=cutoff,
            include_synthetic=include_synthetic,
        )
        quality_ids = [int(row["id"]) for row in quality_rows]
        manual_review = sum(row["status"] == "manual_review_required" for row in quality_rows)
        manual_short_lead = sum(
            row["status"] == "manual_review_required"
            and bool(row["short_lead_time_filtered"])
            for row in quality_rows
        )

        offers_by_job: dict[int, list[sqlite3.Row]] = {job_id: [] for job_id in quality_ids}
        if quality_ids:
            placeholders = ",".join("?" for _ in quality_ids)
            offer_rows = connection.execute(
                f"""
                SELECT job_id, status, price_cents, responded_at
                FROM job_offer
                WHERE job_id IN ({placeholders})
                """,
                quality_ids,
            ).fetchall()
            for row in offer_rows:
                offers_by_job[int(row["job_id"])].append(row)

        with_created_offers = sum(bool(rows) for rows in offers_by_job.values())
        priced_offer_counts = {
            job_id: sum(row["price_cents"] is not None for row in rows)
            for job_id, rows in offers_by_job.items()
        }
        with_one_price = sum(count >= 1 for count in priced_offer_counts.values())
        with_two_prices = sum(count >= 2 for count in priced_offer_counts.values())

        response_seconds: list[float] = []
        created_by_id = {
            int(row["id"]): _parse_timestamp(row["created_at"])
            for row in quality_rows
        }
        for job_id, rows in offers_by_job.items():
            created_at = created_by_id[job_id]
            responses: list[datetime] = []
            for offer_row in rows:
                if offer_row["price_cents"] is None:
                    continue
                responded_at = _parse_timestamp(offer_row["responded_at"])
                if responded_at is not None:
                    responses.append(responded_at)
            if created_at is not None and responses:
                response_seconds.append(max(0.0, (min(responses) - created_at).total_seconds()))

        selected = sum(
            row["assigned_at"] is not None
            or row["status"]
            in {"assigned_pending_confirmation", "assigned", "in_progress", "completed"}
            for row in quality_rows
        )
        assignment_confirmed = sum(
            row["status"] in {"assigned", "in_progress", "completed"}
            for row in quality_rows
        )
        completed = sum(
            row["completed_at"] is not None or row["status"] == "completed"
            for row in quality_rows
        )

        delivery = {
            "coverage_note": (
                "Only jobs represented in telegram_notification_outbox are measured; "
                "the durable outbox was introduced after historical offers."
            ),
            "represented_jobs": 0,
            "sent_jobs": 0,
            "failed_jobs": 0,
        }
        if quality_ids:
            placeholders = ",".join("?" for _ in quality_ids)
            delivery_row = connection.execute(
                f"""
                SELECT
                    COUNT(DISTINCT job_id) AS represented_jobs,
                    COUNT(DISTINCT CASE WHEN delivery_status = 'sent' THEN job_id END) AS sent_jobs,
                    COUNT(DISTINCT CASE WHEN delivery_status = 'failed' THEN job_id END) AS failed_jobs
                FROM telegram_notification_outbox
                WHERE notification_type = 'carrier_offer'
                  AND job_id IN ({placeholders})
                """,
                quality_ids,
            ).fetchone()
            delivery.update({key: int(delivery_row[key]) for key in ("represented_jobs", "sent_jobs", "failed_jobs")})

        event_counters = _event_counters(connection, cutoff=cutoff)
        return {
            "checked_at": checked_at.isoformat(),
            "window": {
                "days": days,
                "start": cutoff.isoformat(),
                "end": checked_at.isoformat(),
            },
            "definitions": {
                "browser_event_counters": "Aggregated event totals, not unique people or cohorts.",
                "confirmed_request": "One non-draft, non-synthetic job row; job.id is the deduplicated unit.",
                "quality_request": (
                    "A confirmed request with requested time, contact, pickup and dropoff, "
                    "and cargo text or item data."
                ),
                "with_created_offers": "At least one persisted job_offer; not proof of real-time availability.",
                "with_price": "At least one persisted offer with price_cents; carrier acceptance may later be closed.",
                "selected": "assigned_at is set or lifecycle reached assignment selection.",
                "completed": "completed_at is set or current lifecycle status is completed.",
                "synthetic_rows": "Excluded by default when source starts with synthetic.",
            },
            "database": {"path": str(database), "quick_check": quick_check},
            "browser_events": event_counters,
            "requests": {
                "confirmed_unique": confirmed_requests,
                "quality_unique": len(quality_ids),
                "quality_rate_of_confirmed": _rate(len(quality_ids), confirmed_requests),
                "manual_review": manual_review,
                "manual_review_rate": _rate(manual_review, len(quality_ids)),
                "manual_short_lead": manual_short_lead,
                "manual_other_reason": manual_review - manual_short_lead,
                "with_created_offers": with_created_offers,
                "with_created_offers_rate": _rate(with_created_offers, len(quality_ids)),
                "with_at_least_one_price": with_one_price,
                "with_at_least_one_price_rate": _rate(with_one_price, len(quality_ids)),
                "with_at_least_two_prices": with_two_prices,
                "with_at_least_two_prices_rate": _rate(with_two_prices, len(quality_ids)),
                "selected": selected,
                "selected_rate": _rate(selected, len(quality_ids)),
                "assignment_confirmed": assignment_confirmed,
                "assignment_confirmed_rate": _rate(assignment_confirmed, len(quality_ids)),
                "completed": completed,
                "completed_rate": _rate(completed, len(quality_ids)),
            },
            "time_to_first_price_seconds": {
                "measured_jobs": len(response_seconds),
                "median": _nearest_rank(response_seconds, 0.5),
                "p90": _nearest_rank(response_seconds, 0.9),
                "without_price_are_excluded_from_latency_only": len(quality_ids) - len(response_seconds),
            },
            "carrier_offer_delivery": delivery,
            "attribution": _source_breakdown(connection, quality_ids=quality_ids),
            "not_measured": {
                "unique_browser_people": "No visitor/session identifier is stored in acquisition_event_daily.",
                "operator_minutes": "No structured operator-time records exist.",
                "disputes_and_quality": "No structured complaint or outcome-quality table exists.",
                "historical_telegram_delivery": "Pre-outbox Telegram sends cannot be reconstructed reliably.",
            },
        }
    finally:
        connection.close()

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read-only CargoPT request outcome and attribution metrics"
    )
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--include-synthetic", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.days <= 0:
        raise SystemExit("--days must be positive")
    report = build_report(
        args.database,
        days=args.days,
        include_synthetic=args.include_synthetic,
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
