import tempfile
from pathlib import Path

from static_release_inventory import (
    StaticInventoryError,
    build_static_inventory,
)


def main() -> None:
    with tempfile.TemporaryDirectory(
        prefix="cargopt_static_inventory_"
    ) as temporary:
        root = Path(temporary)
        source = root / "source"
        webroot = root / "webroot"
        source.mkdir()
        webroot.mkdir()

        (source / "index.html").write_text("CargoPT", encoding="utf-8")
        (webroot / "index.html").write_text("CargoPT", encoding="utf-8")
        private = source / "meta-operations"
        private.mkdir()
        (private / "index.html").write_text("private", encoding="utf-8")

        inventory = build_static_inventory(
            source,
            webroot,
            allowed_source_only=("meta-operations",),
        )
        assert inventory["published_file_count"] == 1
        assert inventory["source_only_files"] == [
            "meta-operations/index.html"
        ]
        assert inventory["static_version"].startswith("sha256:")

        try:
            build_static_inventory(source, webroot)
        except StaticInventoryError as exc:
            assert "STATIC_SOURCE_ONLY_UNDECLARED" in str(exc)
        else:
            raise AssertionError("undeclared source-only file was accepted")

        (webroot / "index.html").write_text("changed", encoding="utf-8")
        try:
            build_static_inventory(
                source,
                webroot,
                allowed_source_only=("meta-operations",),
            )
        except StaticInventoryError as exc:
            assert "STATIC_CONTENT_MISMATCH:index.html" in str(exc)
        else:
            raise AssertionError("mismatched published file was accepted")

    print("STATIC_RELEASE_INVENTORY_SMOKE_OK")


if __name__ == "__main__":
    main()
