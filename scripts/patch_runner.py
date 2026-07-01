from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKUP_ROOT = ROOT / ".patch_backups"


class PatchError(RuntimeError):
    pass


def run(cmd: list[str], *, cwd: Path = ROOT) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def rel_path(path: Path) -> str:
    path = path.resolve()
    if ROOT not in path.parents and path != ROOT:
        raise PatchError(f"Path is outside repo: {path}")
    return str(path.relative_to(ROOT))


def git_status() -> str:
    result = subprocess.run(
        ["git", "status", "-sb"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def load_patch_module(patch_path: Path):
    if not patch_path.exists():
        raise PatchError(f"Patch file not found: {patch_path}")

    spec = importlib.util.spec_from_file_location("user_patch", patch_path)
    if spec is None or spec.loader is None:
        raise PatchError(f"Cannot load patch: {patch_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_targets(module) -> list[Path]:
    raw_targets = getattr(module, "TARGETS", None)
    if not raw_targets:
        raise PatchError("Patch must define TARGETS = [...]")

    targets = []
    for item in raw_targets:
        target = (ROOT / item).resolve()
        rel_path(target)
        targets.append(target)

    return targets


def backup_targets(targets: list[Path]) -> Path:
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%SZ")
    backup_dir = BACKUP_ROOT / stamp
    backup_dir.mkdir(parents=True, exist_ok=False)

    for target in targets:
        if target.exists():
            dest = backup_dir / rel_path(target)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, dest)

    return backup_dir


def restore_backup(backup_dir: Path, targets: list[Path]) -> None:
    for target in targets:
        backup = backup_dir / rel_path(target)
        if backup.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup, target)


def default_verify() -> None:
    run(["git", "diff", "--check"])
    run([sys.executable, "-m", "py_compile", "scripts/patch_runner.py"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("patch_file")
    parser.add_argument("--no-verify", action="store_true")
    args = parser.parse_args()

    print("===== STATUS BEFORE =====")
    print(git_status())

    patch_path = Path(args.patch_file).resolve()
    module = load_patch_module(patch_path)
    targets = get_targets(module)

    print("===== TARGETS =====")
    for target in targets:
        print(rel_path(target))

    backup_dir = backup_targets(targets)
    print(f"===== BACKUP ===== {backup_dir}")

    try:
        if not hasattr(module, "apply"):
            raise PatchError("Patch must define apply(root)")

        module.apply(ROOT)

        if not args.no_verify:
            if hasattr(module, "verify"):
                module.verify(ROOT)
            else:
                default_verify()

    except Exception:
        print("===== PATCH FAILED - ROLLED BACK =====")
        print(traceback.format_exc())
        restore_backup(backup_dir, targets)
        return 1

    print("===== STATUS AFTER =====")
    print(git_status())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
