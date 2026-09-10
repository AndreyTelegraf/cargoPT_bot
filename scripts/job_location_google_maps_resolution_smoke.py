import asyncio
import os
import sys
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/cargopt_dev.db"

import app.services.location_normalization as target


extract_coordinates = target.extract_coordinates
extract_link_query_address = target.extract_link_query_address


def assert_coordinates(value: str, expected: tuple[float, float]) -> None:
    actual = extract_coordinates(value)
    if actual != expected:
        raise AssertionError(f"expected {expected}, got {actual} for {value!r}")


assert_coordinates(
    "https://www.google.com/maps/place/Test/@38.7223,-9.1393,17z",
    (38.7223, -9.1393),
)

assert extract_link_query_address(
    "https://www.google.com/maps/place/"
    "R.+Cap.+Ramires+21,+1000-084+Lisboa/data=!4m2!3m1!1sTest"
) == "R. Cap. Ramires 21, 1000-084 Lisboa"
assert_coordinates(
    "https://www.google.com/maps/search/?api=1&query=38.7223,-9.1393",
    (38.7223, -9.1393),
)
assert_coordinates(
    "https://www.google.com/maps/place/Test/data=!3d38.7223!4d-9.1393",
    (38.7223, -9.1393),
)
assert_coordinates(
    "38.7223, -9.1393",
    (38.7223, -9.1393),
)


assert target.extract_maps_url(
    "https://www.google.com/maps/place/Lisboa"
) == "https://www.google.com/maps/place/Lisboa"
assert target.extract_maps_url(
    "https://maps.app.goo.gl/TrustedToken"
) == "https://maps.app.goo.gl/TrustedToken"
assert target.extract_maps_url(
    "https://google.example.invalid/maps/place/CargoPT"
) is None
assert target.extract_maps_url(
    "https://www.google.com@127.0.0.1/maps/place/CargoPT"
) is None
assert target.extract_maps_url(
    "https://www.google.com:444/maps/place/CargoPT"
) is None


async def assert_ssrf_guards() -> None:
    original_client = target.httpx.AsyncClient
    original_getaddrinfo = target.socket.getaddrinfo
    requested_urls = []

    class StubClient:
        responses = []

        def __init__(self, *args, **kwargs):
            if kwargs.get("follow_redirects") is not False:
                raise AssertionError("maps resolver must validate redirects itself")

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, url):
            requested_urls.append(url)
            return self.responses.pop(0)

    def public_dns(*args, **kwargs):
        return [(2, 1, 6, "", ("8.8.8.8", 443))]

    try:
        target.httpx.AsyncClient = StubClient
        target.socket.getaddrinfo = public_dns

        malicious = "https://google.example.invalid/maps/place/CargoPT"
        assert await target.resolve_google_maps_url(malicious) == malicious
        assert requested_urls == []

        trusted = "https://maps.app.goo.gl/TrustedToken"
        StubClient.responses = [
            SimpleNamespace(
                status_code=302,
                headers={"location": "http://127.0.0.1/private"},
                url=trusted,
            )
        ]
        assert await target.resolve_google_maps_url(trusted) == trusted
        assert requested_urls == [trusted]

        requested_urls.clear()
        target.socket.getaddrinfo = lambda *args, **kwargs: [
            (2, 1, 6, "", ("127.0.0.1", 443))
        ]
        google_url = "https://www.google.com/maps/place/Lisboa"
        assert await target.resolve_google_maps_url(google_url) == google_url
        assert requested_urls == []

        requested_urls.clear()
        target.socket.getaddrinfo = public_dns
        final_url = "https://www.google.com/maps/place/Lisboa/@38.72,-9.13,17z"
        StubClient.responses = [
            SimpleNamespace(
                status_code=302,
                headers={"location": final_url},
                url=trusted,
            ),
            SimpleNamespace(
                status_code=200,
                headers={},
                url=final_url,
            ),
        ]
        assert await target.resolve_google_maps_url(trusted) == final_url
        assert requested_urls == [trusted, final_url]
    finally:
        target.httpx.AsyncClient = original_client
        target.socket.getaddrinfo = original_getaddrinfo


asyncio.run(assert_ssrf_guards())

print("JOB_LOCATION_GOOGLE_MAPS_RESOLUTION_SMOKE_OK")
