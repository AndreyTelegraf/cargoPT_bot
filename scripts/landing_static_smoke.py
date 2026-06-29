import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from app.api.main import app


def main() -> None:
    with TestClient(app) as client:
        checks = {
            "/": "Начните с трёх простых вопросов.",
            "/assets/css/landing.css": "hero-form",
            "/assets/js/landing.js": "landing_static_v2",
            "/health": "ok",
        }

        for path, expected in checks.items():
            response = client.get(path)
            if response.status_code != 200:
                raise SystemExit(f"{path} failed: {response.status_code} {response.text[:200]}")
            if expected not in response.text:
                raise SystemExit(f"{path} missing expected content: {expected}")

    print("LANDING_STATIC_SMOKE_OK")


if __name__ == "__main__":
    main()
