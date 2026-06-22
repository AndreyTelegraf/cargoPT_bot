import compileall
import importlib
import os
import shutil
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
SOURCE_DIRS = [
    PROJECT_ROOT / "app",
    PROJECT_ROOT / "migrations",
    PROJECT_ROOT / "scripts",
    PROJECT_ROOT / "tests",
]

os.environ.setdefault("BOT_TOKEN", "smoke-test-token")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://cargopt:cargopt@localhost:5432/cargopt_smoke",
)
os.environ.setdefault("ENVIRONMENT", "smoke")
os.environ.setdefault("LOG_LEVEL", "INFO")


def remove_pycache() -> None:
    for path in PROJECT_ROOT.rglob("__pycache__"):
        if path.is_dir():
            shutil.rmtree(path)


def compile_sources() -> None:
    failed = False
    for source_dir in SOURCE_DIRS:
        if not source_dir.exists():
            continue
        ok = compileall.compile_dir(
            str(source_dir),
            quiet=1,
            force=True,
            legacy=False,
        )
        failed = failed or not ok

    if failed:
        raise SystemExit("Python compilation failed")


def import_base_modules() -> None:
    modules = [
        "app.config",
        "app.main",
        "app.db.base",
        "app.db.session",
        "app.models",
        "app.models.carrier",
    ]

    for module_name in modules:
        importlib.import_module(module_name)


def main() -> None:
    remove_pycache()
    compile_sources()
    remove_pycache()
    import_base_modules()
    remove_pycache()
    print("SMOKE_OK")


if __name__ == "__main__":
    main()
