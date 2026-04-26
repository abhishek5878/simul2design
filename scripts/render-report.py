#!/usr/bin/env python3
"""
render-report.py — render a client's synthesis report to a preview PNG.

The HTML report at data/<client>/report/index.html is the customer-facing
deliverable. It's currently hand-curated per client (template generalization
is Phase 2 — see INTEGRATION.md).

This script:
1. Validates the report's inputs exist (HTML + mockup).
2. Re-renders the PNG preview via Chrome headless.
3. Prints absolute paths so the user can open both.
4. Exits 0 on success, 1 on missing inputs, 2 on render failure.

Usage:
    scripts/render-report.py <client>
    scripts/render-report.py univest
"""

from __future__ import annotations
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHROME_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]

PREVIEW_W = 1100
PREVIEW_H = 1800
PREVIEW_SCALE = 1.5


def find_chrome() -> str | None:
    for p in CHROME_PATHS:
        if Path(p).exists():
            return p
    return shutil.which("google-chrome") or shutil.which("chromium")


def render(client: str) -> int:
    data_dir = ROOT / "data" / client
    report_dir = data_dir / "report"
    html_path = report_dir / "index.html"
    mockup_path = data_dir / "design" / "v5a-green.png"
    preview_path = report_dir / "preview.png"

    # Validate inputs
    if not data_dir.is_dir():
        print(f"Error: data/{client}/ does not exist", file=sys.stderr)
        return 1
    if not html_path.is_file():
        print(f"Error: {html_path.relative_to(ROOT)} not found", file=sys.stderr)
        print(f"       Hand-curate the report HTML there first (see INTEGRATION.md).", file=sys.stderr)
        return 1
    if not mockup_path.is_file():
        print(f"Warning: {mockup_path.relative_to(ROOT)} not found — report will render a broken image",
              file=sys.stderr)

    chrome = find_chrome()
    if not chrome:
        print("Error: Chrome / Chromium not found. Install one or add it to PATH.", file=sys.stderr)
        return 2

    # Render
    cmd = [
        chrome,
        "--headless",
        "--disable-gpu",
        f"--screenshot={preview_path}",
        f"--window-size={PREVIEW_W},{PREVIEW_H}",
        "--hide-scrollbars",
        f"--force-device-scale-factor={PREVIEW_SCALE}",
        "--virtual-time-budget=2000",
        f"file://{html_path}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0 and not preview_path.exists():
        print(f"Error: Chrome render failed (exit {result.returncode})", file=sys.stderr)
        print(result.stderr[:500], file=sys.stderr)
        return 2

    # Report
    print(f"Report ready for {client}:")
    print(f"  HTML:    {html_path}")
    print(f"  Preview: {preview_path}")
    print(f"  Mockup:  {mockup_path}")
    print()
    print(f"Open in browser:  open '{html_path}'")
    print(f"Open preview:     open '{preview_path}'")
    return 0


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__, file=sys.stderr)
        return 1
    return render(sys.argv[1])


if __name__ == "__main__":
    sys.exit(main())
