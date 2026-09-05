import argparse
import urllib.request
from pathlib import Path
from xml.etree import ElementTree


EXPECTED_DATE = "2026-09-05"
EXPECTED_SITEMAP_DATES = {
    "https://cargopt.pt/": "2026-09-02",
    "https://cargopt.pt/en/": "2026-09-02",
    "https://cargopt.pt/ru/": "2026-09-02",
    "https://cargopt.pt/aeo.md": EXPECTED_DATE,
    "https://cargopt.pt/knowledge.md": EXPECTED_DATE,
    "https://cargopt.pt/privacy/": "2026-09-02",
    "https://cargopt.pt/cookies/": "2026-09-02",
    "https://cargopt.pt/en/privacy/": "2026-09-02",
    "https://cargopt.pt/en/cookies/": "2026-09-02",
    "https://cargopt.pt/ru/privacy/": "2026-09-02",
    "https://cargopt.pt/ru/cookies/": "2026-09-02",
}


def parse_groups(text: str) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    agents: list[str] = []
    for raw_line in [*text.splitlines(), ""]:
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            agents = []
            continue
        key, separator, value = line.partition(":")
        if not separator:
            continue
        key = key.strip().lower()
        value = value.strip()
        if key == "user-agent":
            agents.append(value)
            groups.setdefault(value, [])
        elif agents:
            for agent in agents:
                groups[agent].append(f"{key}:{value}")
    return groups


def check_static(static_root: Path) -> None:
    robots = (static_root / "robots.txt").read_text(encoding="utf-8")
    groups = parse_groups(robots)
    assert "allow:/" in groups.get("OAI-SearchBot", [])
    assert "disallow:/" in groups.get("GPTBot", [])
    assert "allow:/" in groups.get("*", [])

    aeo = (static_root / "aeo.md").read_text(encoding="utf-8")
    knowledge = (static_root / "knowledge.md").read_text(encoding="utf-8")
    assert f"Last updated: {EXPECTED_DATE}" in aeo
    assert f"Last updated: {EXPECTED_DATE}" in knowledge

    root = ElementTree.parse(static_root / "sitemap.xml").getroot()
    namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    values = {}
    for url in root.findall("s:url", namespace):
        location = url.findtext("s:loc", namespaces=namespace)
        last_modified = url.findtext("s:lastmod", namespaces=namespace)
        assert location and location not in values
        values[location] = last_modified
    for location, expected in EXPECTED_SITEMAP_DATES.items():
        assert values.get(location) == expected, (location, values.get(location))


def check_public(base_url: str) -> None:
    for path in ("/aeo.md", "/knowledge.md"):
        request = urllib.request.Request(
            base_url.rstrip("/") + path + "?ai_discovery_smoke=1",
            headers={
                "Cache-Control": "no-cache",
                "User-Agent": "CargoPT manifest deploy verification",
            },
            method="HEAD",
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            assert response.status == 200
            assert response.headers.get_content_type() == "text/markdown"

    request = urllib.request.Request(
        base_url.rstrip("/") + "/robots.txt?ai_discovery_smoke=1",
        headers={
            "Cache-Control": "no-cache",
            "User-Agent": "CargoPT manifest deploy verification",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        groups = parse_groups(response.read().decode("utf-8"))
        assert "allow:/" in groups.get("OAI-SearchBot", [])
        assert "disallow:/" in groups.get("GPTBot", [])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--static-root",
        type=Path,
        default=Path("app/static"),
    )
    parser.add_argument("--public-base-url")
    args = parser.parse_args()
    check_static(args.static_root)
    if args.public_base_url:
        check_public(args.public_base_url)
    print("AI_DISCOVERY_STATIC_SMOKE_OK")


if __name__ == "__main__":
    main()
