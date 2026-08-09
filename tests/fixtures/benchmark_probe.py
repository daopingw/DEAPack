"""Small subprocess probe used only by benchmark-runner tests."""

from __future__ import annotations

import argparse
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("pass", "fail", "sleep"), required=True)
    arguments = parser.parse_args()
    print(f"probe stdout mode={arguments.mode}", flush=True)
    print(f"probe stderr mode={arguments.mode}", file=sys.stderr, flush=True)
    if arguments.mode == "sleep":
        time.sleep(5.0)
    return 7 if arguments.mode == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
