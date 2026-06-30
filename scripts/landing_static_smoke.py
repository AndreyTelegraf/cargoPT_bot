import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from app.api.main import app


def main() -> None:
    with TestClient(app) as client:
        checks = {
            "/": "Comece com três perguntas simples.",
            "/en/": "Start with three simple questions.",
            "/ru/": "Начните с трёх простых вопросов.",
            "/assets/css/landing.css": "locale-switcher",
            "/assets/js/landing.js": "pageLocale",
            "/robots.txt": "Sitemap: https://cargopt.pt/sitemap.xml",
            "/sitemap.xml": "https://cargopt.pt/ru/",
            "/llms.txt": "https://cargopt.pt/aeo.md",
            "/ai.txt": "CargoPT summary for AI assistants",
            "/aeo.md": "CargoPT positions itself as Portugal",
            "/knowledge.md": "Primary keywords",
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
