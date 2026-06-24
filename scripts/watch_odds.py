from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run odds updates repeatedly.")
    parser.add_argument("--interval-minutes", type=float, default=15.0)
    parser.add_argument("--api-key", default=os.getenv("THE_ODDS_API_KEY"))
    parser.add_argument("--once", action="store_true")
    return parser.parse_args()


def run_update(api_key: str | None) -> int:
    env = os.environ.copy()
    if api_key:
        env["THE_ODDS_API_KEY"] = api_key
    command = [sys.executable, str(ROOT / "scripts" / "update_odds.py")]
    result = subprocess.run(command, cwd=ROOT, env=env)
    return result.returncode


def main() -> int:
    args = parse_args()
    if args.interval_minutes <= 0:
        print("--interval-minutes must be greater than 0", file=sys.stderr)
        return 2

    while True:
        code = run_update(args.api_key)
        if args.once:
            return code
        time.sleep(args.interval_minutes * 60)


if __name__ == "__main__":
    raise SystemExit(main())
