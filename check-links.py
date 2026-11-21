#!/usr/bin/env python3
"""Check every link in README.md and report which ones are unreachable.

Usage:
    python3 scripts/check-links.py

Exit code 0 when all links respond, 1 when any link fails. Uses only the
standard library. A link is considered OK when the server answers with a
2xx or 3xx status; 403 from bot-protection (Cloudflare etc.) is reported
as BLOCKED, not as a failure, so a human can check it manually.
"""

import re
import sys
import urllib.request
from pathlib import Path

README = Path(__file__).resolve().parent.parent / "README.md"
URL_RE = re.compile(r"https?://[^\s\)\]<>\"']+")
HEADERS = {"User-Agent": "awesome-ai-indonesia link-checker (GitHub repo maintenance)"}


def check(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return f"OK {resp.status}"
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return "BLOCKED 403 (bot protection, check manually)"
        if e.code in (404, 405, 501):
            # Some sites (Kaggle, SPAs) do not implement HEAD properly;
            # retry with GET before calling it a failure.
            try:
                req = urllib.request.Request(url, headers=HEADERS, method="GET")
                with urllib.request.urlopen(req, timeout=15) as resp:
                    return f"OK {resp.status} (via GET)"
            except Exception as err:  # noqa: BLE001 - report, don't crash
                return f"FAIL {err}"
        return f"FAIL HTTP {e.code}"
    except Exception as err:  # noqa: BLE001 - report, don't crash
        return f"FAIL {err}"


def main() -> int:
    text = README.read_text(encoding="utf-8")
    urls = sorted(set(URL_RE.findall(text)))
    print(f"Checking {len(urls)} links in README.md...\n")
    failures = 0
    for url in urls:
        status = check(url)
        mark = "✓" if status.startswith("OK") else ("~" if status.startswith("BLOCKED") else "✗")
        if status.startswith("FAIL"):
            failures += 1
        print(f"{mark} {status:45} {url}")
    print()
    if failures:
        print(f"{failures} link(s) failed.")
        return 1
    print("All links OK (BLOCKED ones need a manual check).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
