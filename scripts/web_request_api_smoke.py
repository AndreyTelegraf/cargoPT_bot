import os
import shutil
import sqlite3
import subprocess
import sys
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / ".tmp_web_request_api_smoke"
DATABASE_URL = "sqlite+aiosqlite:///.tmp_web_request_api_smoke/cargopt_dev.db"


class FakeBot:
    def __init__(self) -> None:
        self.messages = []

    async def send_message(self, *, chat_id, text, **kwargs):
        self.messages.append((chat_id, text, kwargs))
        raise AssertionError("web request API must not call Telegram directly")


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def reset_db() -> None:
    if DATA_DIR == PROJECT_ROOT / "data":
        raise RuntimeError("smoke must not delete PROJECT_ROOT/data")
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    DATA_DIR.mkdir(exist_ok=True)


def main() -> None:
    os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
    os.environ["DATABASE_URL"] = DATABASE_URL
    os.environ["ENVIRONMENT"] = "web-request-api-smoke"
    os.environ["LOG_LEVEL"] = "INFO"
    os.environ["EMAIL_ENABLED"] = "true"

    reset_db()

    import asyncio
    import app.models  # noqa: F401
    from sqlalchemy.ext.asyncio import create_async_engine
    from app.db.base import Base

    async def create_test_schema() -> None:
        engine = create_async_engine(DATABASE_URL)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    asyncio.run(create_test_schema())

    from fastapi.testclient import TestClient

    from app.api.main import app
    from app.api.web_requests import get_api_bot
    from app.db.session import engine as app_engine

    fake_bot = FakeBot()

    async def override_bot():
        yield fake_bot

    app.dependency_overrides[get_api_bot] = override_bot

    payload = {
        "source_locale": "ru",
        "customer_name": "Web Client",
        "customer_email": "client@example.test",
        "preferred_contact": "whatsapp",
        "client_phone": "+351900000000",
        "client_whatsapp": "+351900000000",
        "utm_source": "landing",
        "utm_medium": "organic",
        "utm_campaign": "lisbon_launch",
        "utm_content": "hero_form",
        "referrer_host": "t.me",
        "fbclid": "test-click-id",
        "landing_version": "v1",
        "requested_date": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
        "addresses": [
            {
                "kind": "pickup",
                "raw_text": "Lisboa",
                "normalized_address": "Lisboa, Portugal",
                "latitude": 38.7077507,
                "longitude": -9.1365919,
                "location_confirmed": True,
                "floor": 2,
                "has_elevator": True,
            },
            {
                "kind": "dropoff",
                "raw_text": "Porto",
                "normalized_address": "Porto, Portugal",
                "latitude": 41.1494512,
                "longitude": -8.6107884,
                "location_confirmed": True,
                "floor": 0,
                "has_elevator": False,
            },
        ],
        "items": [{"description": "10 boxes and washing machine", "quantity": 10}],
        "needs_assembly": False,
        "needs_packing": False,
        "needs_tail_lift": False,
        "needs_crane": False,
        "needs_mobile_lift": False,
        "required_loaders": 2,
        "estimated_payload_kg": 500,
        "estimated_volume_m3": 3.0,
        "comment": "Submitted from web form",
    }

    from pydantic import ValidationError

    from app.api.web_request_schemas import WebRequestPayload

    invalid_payloads = []

    whitespace_contact = dict(payload)
    whitespace_contact.update(
        customer_email=None,
        client_phone="   ",
        client_whatsapp="\t",
    )
    invalid_payloads.append(("whitespace contact", whitespace_contact))

    invalid_email = dict(payload)
    invalid_email.update(
        customer_email="not-an-email",
        client_phone=None,
        client_whatsapp=None,
    )
    invalid_payloads.append(("invalid email", invalid_email))

    blank_cargo = dict(payload)
    blank_cargo["items"] = [{"description": "   ", "quantity": 0}]
    invalid_payloads.append(("blank cargo and zero quantity", blank_cargo))

    duplicate_route = dict(payload)
    duplicate_route["addresses"] = [
        dict(payload["addresses"][0]),
        dict(payload["addresses"][0]),
        dict(payload["addresses"][1]),
        dict(payload["addresses"][1]),
    ]
    invalid_payloads.append(("duplicate route structure", duplicate_route))

    for label, invalid_payload in invalid_payloads:
        try:
            WebRequestPayload.model_validate(invalid_payload)
        except ValidationError:
            pass
        else:
            raise AssertionError(f"invalid web request accepted: {label}")

    normalized_payload = dict(payload)
    normalized_payload.update(
        customer_name="  Web Client  ",
        customer_email="  client@example.test  ",
        client_phone="  +351900000000  ",
    )
    normalized = WebRequestPayload.model_validate(normalized_payload)
    assert normalized.customer_name == "Web Client"
    assert normalized.customer_email == "client@example.test"
    assert normalized.client_phone == "+351900000000"

    local_datetime_payload = dict(payload)
    local_datetime_payload.pop("requested_date")
    local_datetime_payload.update(
        requested_date_local="2026-12-01",
        requested_time_local="14:30",
    )
    local_datetime = WebRequestPayload.model_validate(local_datetime_payload)
    assert local_datetime.requested_date == datetime(
        2026,
        12,
        1,
        14,
        30,
        tzinfo=UTC,
    )

    summer_local_datetime_payload = dict(payload)
    summer_local_datetime_payload.pop("requested_date")
    summer_local_datetime_payload.update(
        requested_date_local="2027-07-01",
        requested_time_local="14:30",
    )
    summer_local_datetime = WebRequestPayload.model_validate(
        summer_local_datetime_payload
    )
    assert summer_local_datetime.requested_date == datetime(
        2027,
        7,
        1,
        13,
        30,
        tzinfo=UTC,
    )

    incomplete_local_datetime = dict(payload)
    incomplete_local_datetime.pop("requested_date")
    incomplete_local_datetime["requested_date_local"] = "2026-12-01"
    try:
        WebRequestPayload.model_validate(incomplete_local_datetime)
    except ValidationError:
        pass
    else:
        raise AssertionError("local requested date without time was accepted")

    with TestClient(app) as client:
        health = client.get("/health")
        if health.status_code != 200:
            raise SystemExit(f"health failed: {health.status_code} {health.text}")

        past_payload = dict(payload)
        past_payload["requested_date"] = "2000-01-01T12:00:00+00:00"
        past_response = client.post("/api/v1/requests", json=past_payload)
        if past_response.status_code != 422:
            raise SystemExit(
                "past date was not rejected: "
                f"{past_response.status_code} {past_response.text}"
            )

        unconfirmed_payload = dict(payload)
        unconfirmed_payload["addresses"] = [
            dict(address) for address in payload["addresses"]
        ]
        unconfirmed_payload["addresses"][0]["location_confirmed"] = False
        unconfirmed_response = client.post(
            "/api/v1/requests",
            json=unconfirmed_payload,
        )
        if unconfirmed_response.status_code != 422:
            raise SystemExit(
                "unconfirmed address was not rejected: "
                f"{unconfirmed_response.status_code} {unconfirmed_response.text}"
            )

        response = client.post("/api/v1/requests", json=payload)
        tracking_response = client.get(
            f"/api/v1/track/{response.json()['tracking_token']}"
        )
        date_change_response = client.post(
            f"/api/v1/track/{response.json()['tracking_token']}"
            "/requested-date",
            json={
                "requested_date_local": "2027-01-15",
                "requested_time_local": "12:45",
            },
        )
        changed_tracking_response = client.get(
            f"/api/v1/track/{response.json()['tracking_token']}"
        )
        cancel_response = client.post(
            f"/api/v1/track/{response.json()['tracking_token']}/cancel"
        )
        repeated_cancel_response = client.post(
            f"/api/v1/track/{response.json()['tracking_token']}/cancel"
        )
        cancelled_date_change_response = client.post(
            f"/api/v1/track/{response.json()['tracking_token']}"
            "/requested-date",
            json={
                "requested_date_local": "2027-01-16",
                "requested_time_local": "13:15",
            },
        )

    app.dependency_overrides.clear()
    asyncio.run(app_engine.dispose())

    if response.status_code != 200:
        raise SystemExit(f"unexpected response: {response.status_code} {response.text}")

    body = response.json()
    if not body.get("job_id"):
        raise SystemExit("job_id missing")
    if body.get("status") != "manual_review_required":
        raise SystemExit(f"unexpected status: {body.get('status')}")
    if not body.get("tracking_token"):
        raise SystemExit("tracking_token missing")
    tracking_prefix = {
        "en": "/en/track",
        "ru": "/ru/track",
    }.get(payload.get("source_locale"), "/track")
    expected_tracking_url = f"{tracking_prefix}/{body['tracking_token']}"
    if body.get("tracking_url") != expected_tracking_url:
        raise SystemExit(
            f"unexpected tracking_url: "
            f"{body.get('tracking_url')} != {expected_tracking_url}"
        )
    if body.get("offers_count") != 0:
        raise SystemExit(f"unexpected offers_count: {body.get('offers_count')}")
    if body.get("sent_count") != 0:
        raise SystemExit(f"unexpected sent_count: {body.get('sent_count')}")
    if "queued_count" not in body or body["queued_count"] != 0:
        raise SystemExit(f"unexpected queued_count: {body.get('queued_count')}")
    if fake_bot.messages:
        raise SystemExit("manual review called Telegram before outbox dispatch")

    if tracking_response.status_code != 200:
        raise SystemExit(
            "tracking request failed: "
            f"{tracking_response.status_code} {tracking_response.text}"
        )
    tracking_details = tracking_response.json().get("request_details")
    if tracking_details is None:
        raise SystemExit("tracking request details missing")
    for field in (
        "customer_name",
        "customer_email",
        "preferred_contact",
        "client_phone",
        "client_whatsapp",
        "requested_date",
        "addresses",
        "items",
        "needs_assembly",
        "needs_packing",
        "needs_tail_lift",
        "needs_crane",
        "needs_mobile_lift",
        "required_loaders",
        "estimated_payload_kg",
        "estimated_volume_m3",
        "comment",
    ):
        if field not in tracking_details:
            raise SystemExit(f"tracking request detail missing: {field}")
    if tracking_details["customer_name"] != payload["customer_name"]:
        raise SystemExit("tracking customer name mismatch")
    actual_requested_date = datetime.fromisoformat(
        tracking_details["requested_date"]
    ).replace(tzinfo=None)
    expected_requested_date = datetime.fromisoformat(
        payload["requested_date"]
    ).replace(tzinfo=None)
    if actual_requested_date != expected_requested_date:
        raise SystemExit("tracking requested date mismatch")
    if tracking_details["addresses"] != [
        {
            "kind": "pickup",
            "raw_text": "Lisboa",
            "normalized_address": "Lisboa, Portugal",
            "country_code": "pt",
            "postal_code": None,
            "address_details": None,
            "floor": 2,
            "has_elevator": True,
        },
        {
            "kind": "dropoff",
            "raw_text": "Porto",
            "normalized_address": "Porto, Portugal",
            "country_code": "pt",
            "postal_code": None,
            "address_details": None,
            "floor": 0,
            "has_elevator": False,
        },
    ]:
        raise SystemExit(
            f"tracking addresses mismatch: {tracking_details['addresses']}"
        )
    if tracking_details["items"] != payload["items"]:
        raise SystemExit("tracking items mismatch")
    if tracking_details["required_loaders"] != 2:
        raise SystemExit("tracking access requirements mismatch")
    if tracking_details["estimated_payload_kg"] != 500:
        raise SystemExit("tracking payload mismatch")
    if tracking_details["estimated_volume_m3"] != 3.0:
        raise SystemExit("tracking volume mismatch")
    if tracking_details["comment"] != payload["comment"]:
        raise SystemExit("tracking comment mismatch")
    if date_change_response.status_code != 200:
        raise SystemExit(
            "tracking date change failed: "
            f"{date_change_response.status_code} {date_change_response.text}"
        )
    changed_date = date_change_response.json()
    if changed_date != {
        "job_id": body["job_id"],
        "status": "manual_review_required",
        "previous_status": "manual_review_required",
        "requested_date": "2027-01-15T12:45:00",
        "repricing_required": False,
    }:
        raise SystemExit(f"unexpected tracking date change: {changed_date}")
    if (
        changed_tracking_response.json()["request_details"]["requested_date"]
        not in {"2027-01-15T12:45:00", "2027-01-15T12:45:00Z"}
    ):
        raise SystemExit("changed date missing from tracking read model")
    if cancel_response.status_code != 200:
        raise SystemExit(
            "tracking cancellation failed: "
            f"{cancel_response.status_code} {cancel_response.text}"
        )
    if cancel_response.json() != {
        "job_id": body["job_id"],
        "status": "cancelled",
        "cancelled_from_status": "manual_review_required",
    }:
        raise SystemExit(
            f"unexpected tracking cancellation: {cancel_response.json()}"
        )
    if repeated_cancel_response.status_code != 409:
        raise SystemExit(
            "repeated tracking cancellation was not rejected: "
            f"{repeated_cancel_response.status_code} "
            f"{repeated_cancel_response.text}"
        )
    if cancelled_date_change_response.status_code != 409:
        raise SystemExit(
            "date change after cancellation was not rejected: "
            f"{cancelled_date_change_response.status_code} "
            f"{cancelled_date_change_response.text}"
        )

    connection = sqlite3.connect(DATA_DIR / "cargopt_dev.db")
    try:
        notifications = connection.execute(
            """
            SELECT job_id, notification_type, delivery_status, count(*)
            FROM telegram_notification_outbox
            GROUP BY job_id, notification_type, delivery_status
            """
        ).fetchall()
        cancellation_events = connection.execute(
            """
            SELECT from_status, to_status, count(*)
            FROM job_status_event
            WHERE job_id = ? AND to_status = 'cancelled'
            GROUP BY from_status, to_status
            """,
            (body["job_id"],),
        ).fetchall()
        cancellation_emails = connection.execute(
            """
            SELECT event_type, status_snapshot, delivery_status, count(*)
            FROM job_email_notification
            WHERE job_id = ? AND event_type = 'request_cancelled'
            GROUP BY event_type, status_snapshot, delivery_status
            """,
            (body["job_id"],),
        ).fetchall()
    finally:
        connection.close()
    expected_notification = (
        body["job_id"],
        "manual_review",
        "pending",
        1,
    )
    if notifications != [expected_notification]:
        raise SystemExit(
            "unexpected manual review outbox state: "
            f"{notifications} != {[expected_notification]}"
        )
    if cancellation_events != [
        ("manual_review_required", "cancelled", 1)
    ]:
        raise SystemExit(
            f"unexpected cancellation events: {cancellation_events}"
        )
    if cancellation_emails != [
        ("request_cancelled", "cancelled", "pending", 1)
    ]:
        raise SystemExit(
            f"unexpected cancellation email state: {cancellation_emails}"
        )

    shutil.rmtree(DATA_DIR)
    print("WEB_REQUEST_API_SMOKE_OK")


if __name__ == "__main__":
    main()
