from pathlib import Path

from fastapi.testclient import TestClient

from app.api.main import app
from app.api.main import _is_private_tracking_path


def main() -> None:
    static_dir = Path("app/static")
    assert (static_dir / "track" / "index.html").is_file()
    assert (static_dir / "assets" / "js" / "track.js").is_file()
    assert (static_dir / "assets" / "css" / "track.css").is_file()

    html = (static_dir / "track" / "index.html").read_text()
    js = (static_dir / "assets" / "js" / "track.js").read_text()
    css = (static_dir / "assets" / "css" / "track.css").read_text()
    main_source = Path("app/api/main.py").read_text()

    assert "/assets/js/track.js" in html
    assert "/assets/css/track.css" in html
    assert "tracking-short-lead-warning" in css
    assert "/api/v1/track/" in js
    assert "window.setInterval" in js
    assert "accepted_offers" in js
    assert "track/{tracking_token}" in main_source

    paths = app.openapi()["paths"]
    assert "/api/v1/track/{tracking_token}" in paths

    route_paths = {
        getattr(route, "path", "")
        for route in app.routes
        if hasattr(route, "path")
    }
    assert "/track/{tracking_token}" in route_paths

    assert _is_private_tracking_path("/api/v1/track/private-token")
    assert _is_private_tracking_path("/track/private-token")
    assert _is_private_tracking_path("/en/track/private-token")
    assert _is_private_tracking_path("/ru/track/private-token")
    assert not _is_private_tracking_path("/health")

    with TestClient(app) as client:
        for path in (
            "/track/private-token",
            "/en/track/private-token",
            "/ru/track/private-token",
        ):
            response = client.get(path)
            assert response.status_code == 200
            assert "no-store" in response.headers["cache-control"]
            assert response.headers["pragma"] == "no-cache"
            assert response.headers["referrer-policy"] == "no-referrer"
            assert "noindex" in response.headers["x-robots-tag"]

    print("job_tracking_page_static_ok")


if __name__ == "__main__":
    main()
