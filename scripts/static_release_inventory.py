import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable


DEFAULT_WEBROOT = Path("/var/www/cargopt.pt")
DEFAULT_DATABASE = Path("data/cargopt_prod.db")


class StaticInventoryError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def regular_files(root: Path) -> dict[str, Path]:
    if not root.is_dir():
        raise StaticInventoryError(f"STATIC_ROOT_MISSING:{root}")

    files: dict[str, Path] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise StaticInventoryError(f"STATIC_SYMLINK_UNSUPPORTED:{path}")
        if path.is_file():
            files[path.relative_to(root).as_posix()] = path
    return files


def path_is_allowed(relative: str, allowlist: Iterable[str]) -> bool:
    for raw_prefix in allowlist:
        prefix = raw_prefix.strip("/")
        if prefix and (
            relative == prefix or relative.startswith(prefix + "/")
        ):
            return True
    return False


def build_static_inventory(
    source_root: Path,
    webroot: Path,
    *,
    allowed_source_only: Iterable[str] = (),
) -> dict:
    source_files = regular_files(source_root)
    published_files = regular_files(webroot)
    allowed_source_only = tuple(allowed_source_only)

    webroot_only = sorted(published_files.keys() - source_files.keys())
    if webroot_only:
        raise StaticInventoryError(
            "STATIC_WEBROOT_ONLY:" + ",".join(webroot_only)
        )

    source_only = sorted(source_files.keys() - published_files.keys())
    unexpected_source_only = [
        relative
        for relative in source_only
        if not path_is_allowed(relative, allowed_source_only)
    ]
    if unexpected_source_only:
        raise StaticInventoryError(
            "STATIC_SOURCE_ONLY_UNDECLARED:"
            + ",".join(unexpected_source_only)
        )

    entries = []
    mismatches = []
    for relative, live_path in published_files.items():
        source_path = source_files[relative]
        source_sha = sha256(source_path)
        live_sha = sha256(live_path)
        if source_sha != live_sha:
            mismatches.append(relative)
        entries.append(
            {
                "path": relative,
                "sha256": source_sha,
                "size": source_path.stat().st_size,
            }
        )

    if mismatches:
        raise StaticInventoryError(
            "STATIC_CONTENT_MISMATCH:" + ",".join(mismatches)
        )

    version_digest = hashlib.sha256()
    for entry in entries:
        version_digest.update(
            (
                f"{entry['path']}\0{entry['sha256']}\0{entry['size']}\n"
            ).encode("utf-8")
        )

    return {
        "static_version": "sha256:" + version_digest.hexdigest(),
        "published_file_count": len(entries),
        "files": entries,
        "source_only_files": source_only,
        "source_only_allowlist": list(allowed_source_only),
    }


def git_output(repository: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=repository,
        text=True,
    ).strip()


def database_revisions(database: Path) -> list[str]:
    database = database.resolve()
    connection = sqlite3.connect(
        f"file:{database}?mode=ro",
        uri=True,
    )
    try:
        rows = connection.execute(
            "SELECT version_num FROM alembic_version ORDER BY version_num"
        ).fetchall()
    finally:
        connection.close()
    return [str(row[0]) for row in rows]


def build_release_inventory(
    repository: Path,
    source_root: Path,
    webroot: Path,
    database: Path,
    *,
    allowed_source_only: Iterable[str] = (),
) -> dict:
    repository = repository.resolve()
    tracked_static_changes = git_output(
        repository,
        "status",
        "--porcelain",
        "--untracked-files=no",
        "--",
        str(source_root.relative_to(repository)),
    )
    if tracked_static_changes:
        raise StaticInventoryError(
            "TRACKED_STATIC_WORKTREE_DIRTY:" + tracked_static_changes
        )

    static_inventory = build_static_inventory(
        source_root,
        webroot,
        allowed_source_only=allowed_source_only,
    )
    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "repository": str(repository),
        "branch": git_output(repository, "branch", "--show-current"),
        "backend_sha": git_output(repository, "rev-parse", "HEAD"),
        "database": {
            "path": str(database.resolve()),
            "alembic_revisions": database_revisions(database),
        },
        "static": {
            "source_root": str(source_root.resolve()),
            "webroot": str(webroot.resolve()),
            **static_inventory,
        },
        "cdn": {
            "byte_parity_scope": "origin webroot only",
            "note": (
                "CDN cache and HTML injection are verified separately; "
                "they are not treated as origin file differences."
            ),
        },
    }


def write_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def verify_release_inventory(
    record: dict,
    repository: Path,
    source_root: Path,
    webroot: Path,
    database: Path,
) -> dict:
    if record.get("schema_version") != 1:
        raise StaticInventoryError("UNSUPPORTED_RELEASE_INVENTORY_SCHEMA")

    expected_sha = record.get("backend_sha")
    actual_sha = git_output(repository, "rev-parse", "HEAD")
    if expected_sha != actual_sha:
        raise StaticInventoryError(
            f"BACKEND_SHA_MISMATCH:{expected_sha}:{actual_sha}"
        )

    expected_revisions = record.get("database", {}).get(
        "alembic_revisions"
    )
    actual_revisions = database_revisions(database)
    if expected_revisions != actual_revisions:
        raise StaticInventoryError(
            "DATABASE_REVISION_MISMATCH:"
            f"{expected_revisions}:{actual_revisions}"
        )

    expected_static = record.get("static", {})
    actual_static = build_static_inventory(
        source_root,
        webroot,
        allowed_source_only=expected_static.get(
            "source_only_allowlist",
            (),
        ),
    )
    for key in (
        "static_version",
        "published_file_count",
        "files",
        "source_only_files",
    ):
        if expected_static.get(key) != actual_static.get(key):
            raise StaticInventoryError(f"STATIC_RECORD_MISMATCH:{key}")
    return actual_static


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record or verify the CargoPT production release identity."
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", type=Path)
    action.add_argument("--verify", type=Path)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--static-root", type=Path)
    parser.add_argument("--webroot", type=Path, default=DEFAULT_WEBROOT)
    parser.add_argument("--database", type=Path)
    parser.add_argument(
        "--allow-source-only",
        action="append",
        default=[],
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository = args.repository.resolve()
    source_root = (
        args.static_root.resolve()
        if args.static_root
        else repository / "app/static"
    )
    database = (
        args.database.resolve()
        if args.database
        else repository / DEFAULT_DATABASE
    )

    if args.write:
        record = build_release_inventory(
            repository,
            source_root,
            args.webroot,
            database,
            allowed_source_only=args.allow_source_only,
        )
        write_json_atomic(args.write, record)
        action = "WRITTEN"
        result = record["static"]
    else:
        record = json.loads(args.verify.read_text(encoding="utf-8"))
        result = verify_release_inventory(
            record,
            repository,
            source_root,
            args.webroot,
            database,
        )
        action = "VERIFIED"

    print(
        "STATIC_RELEASE_INVENTORY_" + action,
        result["published_file_count"],
        result["static_version"],
    )


if __name__ == "__main__":
    main()
