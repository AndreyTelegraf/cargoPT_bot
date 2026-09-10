import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
JS_PATH = ROOT / "app/static/assets/js/landing.js"


NODE_PROBE = r'''
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync(process.argv[2], "utf8");
const start = source.indexOf("function isValidCalendarDate");
const end = source.indexOf("function buildPayload", start);
if (start < 0 || end < 0) throw new Error("requested date helper block not found");
const context = {Date, Intl, Object};
vm.runInNewContext(source.slice(start, end), context, {filename: "landing.js"});
const explicit = context.normalizeRequestedDate("01/12/2026");
if (explicit !== "2026-12-01") {
  throw new Error(`calendar date shifted in ${process.env.TZ}: ${explicit}`);
}
if (context.normalizeRequestedDate("2026-12-01") !== "2026-12-01") {
  throw new Error(`ISO calendar date shifted in ${process.env.TZ}`);
}
if (context.normalizeRequestedDate("any day") !== null) {
  throw new Error("flexible requested date must remain unset");
}
console.log(`WEB_REQUEST_DATETIME_FRONTEND_OK ${process.env.TZ}`);
'''


def main() -> None:
    for timezone in ("Pacific/Kiritimati", "America/Adak"):
        environment = dict(os.environ)
        environment["TZ"] = timezone
        probe = subprocess.run(
            ["node", "-", str(JS_PATH)],
            input=NODE_PROBE,
            text=True,
            capture_output=True,
            check=False,
            env=environment,
        )
        assert probe.returncode == 0, probe.stderr
        assert f"WEB_REQUEST_DATETIME_FRONTEND_OK {timezone}" in probe.stdout

    print("WEB_REQUEST_DATETIME_FRONTEND_SMOKE_OK")


if __name__ == "__main__":
    main()
