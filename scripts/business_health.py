from __future__ import annotations

import argparse
from collections import Counter
from datetime import UTC, datetime, timedelta
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
from typing import Any


DEFAULT_DATABASE = Path("/opt/bots/cargoPT_bot/data/cargopt_prod.db")
DEFAULT_BACKUP_DIR = Path("/var/lib/cargopt-backups")
TIMER_UNITS = (
    "cargopt_email_dispatch.timer",
    "cargopt_telegram_dispatch.timer",
    "cargopt_backup.timer",
    "cargopt_regression.timer",
)
ONESHOT_UNITS = (
    "cargopt_email_dispatch.service",
    "cargopt_telegram_dispatch.service",
    "cargopt_backup.service",
    "cargopt_regression.service",
)
SCHEDULER_FAILURE_MARKERS = (
    "offer_expiry_job failed",
    "assignment_timeout_job failed",
    "job_lifecycle_notifications failed",
    "subscription_reminder_job failed",
)


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _age_seconds(value: str | None, now: datetime) -> int | None:
    parsed = _parse_timestamp(value)
    if parsed is None:
        return None
    return max(0, int((now - parsed).total_seconds()))


def _recipient_key(value: object) -> str:
    digest = hashlib.sha256(str(value).encode("utf-8")).hexdigest()
    return digest[:12]


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )


def _systemd_value(unit: str, property_name: str) -> str:
    result = _run(
        ["systemctl", "show", unit, f"--property={property_name}", "--value"]
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"cannot inspect {unit}")
    return result.stdout.strip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _add_issue(
    issues: list[dict[str, Any]],
    severity: str,
    signal: str,
    detail: str,
) -> None:
    issues.append({"severity": severity, "signal": signal, "detail": detail})


def _inspect_queue(
    connection: sqlite3.Connection,
    *,
    table: str,
    recipient_column: str,
    now: datetime,
    max_queue_age_seconds: int,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    rows = connection.execute(
        f"""
        SELECT id, job_id, delivery_status, created_at, updated_at,
               next_attempt_at, last_attempt_at, last_error,
               {recipient_column} AS recipient
        FROM {table}
        """
    ).fetchall()
    counts = Counter(row["delivery_status"] for row in rows)
    stalled: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for row in rows:
        status = row["delivery_status"]
        if status in {"pending", "retry"}:
            due_at = _parse_timestamp(row["next_attempt_at"])
            if due_at is not None and due_at > now:
                continue
            reference = row["next_attempt_at"] or row["created_at"]
        elif status == "sending":
            reference = row["last_attempt_at"] or row["updated_at"]
        else:
            reference = None

        age = _age_seconds(reference, now)
        if age is not None and age > max_queue_age_seconds:
            stalled.append(
                {
                    "id": row["id"],
                    "job_id": row["job_id"],
                    "status": status,
                    "age_seconds": age,
                }
            )

        if status == "failed":
            failures.append(
                {
                    "id": row["id"],
                    "job_id": row["job_id"],
                    "recipient_key": _recipient_key(row["recipient"]),
                    "last_error": (row["last_error"] or "")[:160],
                }
            )

    if stalled:
        _add_issue(
            issues,
            "critical",
            f"{table}.stalled",
            f"{len(stalled)} due notification(s) older than threshold",
        )
    if failures:
        _add_issue(
            issues,
            "warning",
            f"{table}.failed",
            f"{len(failures)} terminal failure(s) require review",
        )

    return {
        "counts": dict(sorted(counts.items())),
        "stalled": stalled,
        "failures": failures,
    }


def _inspect_database(
    database: Path,
    *,
    now: datetime,
    max_queue_age_seconds: int,
    max_manual_age_seconds: int,
    delivery_lookback_seconds: int,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        quick_check = connection.execute("PRAGMA quick_check").fetchone()[0]
        foreign_key_issues = len(
            connection.execute("PRAGMA foreign_key_check").fetchall()
        )
        if quick_check != "ok":
            _add_issue(issues, "critical", "database.quick_check", quick_check)
        if foreign_key_issues:
            _add_issue(
                issues,
                "critical",
                "database.foreign_keys",
                f"{foreign_key_issues} violation(s)",
            )

        email = _inspect_queue(
            connection,
            table="job_email_notification",
            recipient_column="recipient_email",
            now=now,
            max_queue_age_seconds=max_queue_age_seconds,
            issues=issues,
        )
        telegram = _inspect_queue(
            connection,
            table="telegram_notification_outbox",
            recipient_column="recipient_chat_id",
            now=now,
            max_queue_age_seconds=max_queue_age_seconds,
            issues=issues,
        )

        manual_rows = connection.execute(
            """
            SELECT id, created_at, updated_at
            FROM job
            WHERE status = ?
            ORDER BY created_at
            """,
            ("manual_review_required",),
        ).fetchall()
        overdue_manual = [
            {
                "job_id": row["id"],
                "age_seconds": _age_seconds(row["created_at"], now),
            }
            for row in manual_rows
            if (_age_seconds(row["created_at"], now) or 0)
            > max_manual_age_seconds
        ]
        if overdue_manual:
            _add_issue(
                issues,
                "warning",
                "jobs.manual_review_overdue",
                f"{len(overdue_manual)} manual job(s) older than threshold",
            )

        lookback_start = now - timedelta(seconds=delivery_lookback_seconds)
        delivery_gaps = connection.execute(
            """
            SELECT j.id, j.status, j.created_at
            FROM job AS j
            WHERE j.created_at >= ?
              AND j.status IN (?, ?)
              AND EXISTS (
                  SELECT 1 FROM job_offer AS offer WHERE offer.job_id = j.id
              )
              AND NOT EXISTS (
                  SELECT 1
                  FROM telegram_notification_outbox AS outbox
                  WHERE outbox.job_id = j.id
              )
            ORDER BY j.created_at
            """,
            (
                lookback_start.replace(tzinfo=None).isoformat(sep=" "),
                "matching",
                "offered",
            ),
        ).fetchall()
        delivery_gap_items = [
            {
                "job_id": row["id"],
                "status": row["status"],
                "age_seconds": _age_seconds(row["created_at"], now),
            }
            for row in delivery_gaps
        ]
        if delivery_gap_items:
            _add_issue(
                issues,
                "critical",
                "jobs.telegram_delivery_gap",
                f"{len(delivery_gap_items)} recent distributed job(s) lack outbox rows",
            )

        offer_counts = dict(
            connection.execute(
                "SELECT status, COUNT(*) FROM job_offer GROUP BY status"
            ).fetchall()
        )
        return {
            "path": str(database),
            "quick_check": quick_check,
            "foreign_key_issues": foreign_key_issues,
            "email_queue": email,
            "telegram_queue": telegram,
            "manual_review": {
                "count": len(manual_rows),
                "overdue": overdue_manual,
            },
            "recent_delivery_gaps": delivery_gap_items,
            "offer_counts": dict(sorted(offer_counts.items())),
        }
    finally:
        connection.close()


def _inspect_backup(
    backup_dir: Path,
    *,
    now: datetime,
    max_backup_age_seconds: int,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    backups = sorted(backup_dir.glob("*.sqlite3"), key=lambda path: path.stat().st_mtime)
    if not backups:
        _add_issue(issues, "critical", "backup.missing", "no SQLite backup found")
        return {"directory": str(backup_dir), "present": False}

    latest = backups[-1]
    modified_at = datetime.fromtimestamp(latest.stat().st_mtime, tz=UTC)
    age_seconds = max(0, int((now - modified_at).total_seconds()))
    checksum_path = latest.with_suffix(latest.suffix + ".sha256")
    checksum_ok = False
    if checksum_path.is_file():
        expected = checksum_path.read_text(encoding="utf-8").split()[0]
        checksum_ok = expected == _sha256(latest)

    connection = sqlite3.connect(f"file:{latest}?mode=ro", uri=True)
    try:
        quick_check = connection.execute("PRAGMA quick_check").fetchone()[0]
        foreign_key_issues = len(
            connection.execute("PRAGMA foreign_key_check").fetchall()
        )
    finally:
        connection.close()

    if age_seconds > max_backup_age_seconds:
        _add_issue(
            issues,
            "critical",
            "backup.stale",
            f"latest backup is {age_seconds} seconds old",
        )
    if not checksum_ok:
        _add_issue(issues, "critical", "backup.checksum", "checksum mismatch")
    if quick_check != "ok" or foreign_key_issues:
        _add_issue(
            issues,
            "critical",
            "backup.integrity",
            f"quick_check={quick_check}; foreign_key_issues={foreign_key_issues}",
        )

    return {
        "directory": str(backup_dir),
        "present": True,
        "latest": latest.name,
        "age_seconds": age_seconds,
        "checksum_ok": checksum_ok,
        "quick_check": quick_check,
        "foreign_key_issues": foreign_key_issues,
    }


def _inspect_systemd(issues: list[dict[str, Any]]) -> dict[str, Any]:
    units: dict[str, dict[str, str]] = {}
    for unit in (*TIMER_UNITS, *ONESHOT_UNITS, "cargopt_bot.service"):
        try:
            active_state = _systemd_value(unit, "ActiveState")
            result = _systemd_value(unit, "Result")
        except Exception as exc:
            units[unit] = {"error": str(exc)}
            _add_issue(issues, "critical", f"systemd.{unit}", str(exc))
            continue
        units[unit] = {"active_state": active_state, "result": result}
        if unit in TIMER_UNITS and active_state != "active":
            _add_issue(
                issues,
                "critical",
                f"systemd.{unit}",
                f"active_state={active_state}",
            )
        if unit == "cargopt_bot.service" and active_state != "active":
            _add_issue(
                issues,
                "critical",
                "scheduler.bot_process",
                f"active_state={active_state}",
            )
        if unit in ONESHOT_UNITS and result not in {"success", ""}:
            _add_issue(
                issues,
                "critical",
                f"systemd.{unit}",
                f"result={result}",
            )

    journal = _run(
        [
            "journalctl",
            "-u",
            "cargopt_bot.service",
            "--since",
            "24 hours ago",
            "--no-pager",
            "--quiet",
        ]
    )
    scheduler_failures = [
        line
        for line in journal.stdout.splitlines()
        if any(marker in line for marker in SCHEDULER_FAILURE_MARKERS)
    ]
    if journal.returncode != 0:
        _add_issue(
            issues,
            "warning",
            "scheduler.journal",
            journal.stderr.strip() or "journal unavailable",
        )
    if scheduler_failures:
        _add_issue(
            issues,
            "critical",
            "scheduler.failures",
            f"{len(scheduler_failures)} failure marker(s) in 24 hours",
        )

    return {
        "units": units,
        "failure_markers_24h": scheduler_failures[-20:],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit CargoPT business health")
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR)
    parser.add_argument("--max-queue-age-seconds", type=int, default=600)
    parser.add_argument("--max-manual-age-seconds", type=int, default=86400)
    parser.add_argument("--delivery-lookback-seconds", type=int, default=86400)
    parser.add_argument("--max-backup-age-seconds", type=int, default=108000)
    parser.add_argument("--skip-backup", action="store_true")
    parser.add_argument("--skip-systemd", action="store_true")
    args = parser.parse_args()

    now = datetime.now(UTC)
    issues: list[dict[str, Any]] = []
    report: dict[str, Any] = {
        "checked_at": now.isoformat(),
        "database": _inspect_database(
            args.database,
            now=now,
            max_queue_age_seconds=args.max_queue_age_seconds,
            max_manual_age_seconds=args.max_manual_age_seconds,
            delivery_lookback_seconds=args.delivery_lookback_seconds,
            issues=issues,
        ),
    }
    if not args.skip_backup:
        report["backup"] = _inspect_backup(
            args.backup_dir,
            now=now,
            max_backup_age_seconds=args.max_backup_age_seconds,
            issues=issues,
        )
    if not args.skip_systemd:
        report["systemd"] = _inspect_systemd(issues)

    severities = {issue["severity"] for issue in issues}
    if "critical" in severities:
        report["status"] = "critical"
        exit_code = 2
    elif "warning" in severities:
        report["status"] = "warning"
        exit_code = 1
    else:
        report["status"] = "ok"
        exit_code = 0
    report["issues"] = issues
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
