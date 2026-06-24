from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from worldcup_predictor.odds_api import (  # noqa: E402
    DEFAULT_MARKETS,
    DEFAULT_REGIONS,
    DEFAULT_SPORT,
    OddsApiConfig,
    fetch_odds,
    normalize_odds_response,
    write_raw_snapshot,
    write_status,
)
from worldcup_predictor.monitoring import append_odds_history, filter_outlier_odds  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch and standardize The Odds API data.")
    parser.add_argument("--api-key", default=os.getenv("THE_ODDS_API_KEY"))
    parser.add_argument("--sport", default=DEFAULT_SPORT)
    parser.add_argument("--regions", default=DEFAULT_REGIONS)
    parser.add_argument("--markets", default=DEFAULT_MARKETS)
    parser.add_argument("--bookmakers", default=None)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "odds_live.csv")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.api_key:
        print("Missing API key. Set THE_ODDS_API_KEY or pass --api-key.", file=sys.stderr)
        return 2

    matches = pd.read_csv(args.data_dir / "matches.csv")
    team_aliases = pd.read_csv(args.data_dir / "team_aliases.csv")
    previous_path = args.output if args.output.exists() else args.data_dir / "odds.csv"
    previous_odds = pd.read_csv(previous_path) if previous_path.exists() else pd.DataFrame()

    config = OddsApiConfig(
        api_key=args.api_key,
        sport=args.sport,
        regions=args.regions,
        markets=args.markets,
        bookmakers=args.bookmakers,
    )
    events, usage_headers = fetch_odds(config)
    raw_path = write_raw_snapshot(events, args.data_dir / "odds_raw")
    odds, unmatched = normalize_odds_response(
        events,
        matches,
        team_aliases=team_aliases,
        previous_odds=previous_odds,
        include_unlisted_events=True,
    )
    raw_row_count = len(odds)
    odds = filter_outlier_odds(odds)

    if odds.empty:
        write_status(
            args.data_dir / "odds_api_status.json",
            rows=0,
            raw_path=raw_path,
            config=config,
            usage_headers=usage_headers,
            unmatched_events=unmatched,
        )
        print("No matching odds rows were produced. Check team aliases and match list.", file=sys.stderr)
        if usage_headers:
            print(f"Usage: {usage_headers}")
        if unmatched:
            print(f"Unmatched events: {len(unmatched)}")
        return 1

    if args.dry_run:
        print(odds.head(20).to_string(index=False))
        print(f"Rows: {len(odds)}")
        print(f"Filtered outlier rows: {raw_row_count - len(odds)}")
        print(f"Raw: {raw_path}")
        if unmatched:
            print(f"Unmatched events: {len(unmatched)}")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    odds.to_csv(args.output, index=False, encoding="utf-8")
    append_odds_history(odds, args.data_dir / "odds_history.csv")
    write_status(
        args.data_dir / "odds_api_status.json",
        rows=len(odds),
        raw_path=raw_path,
        config=config,
        usage_headers=usage_headers,
        unmatched_events=unmatched,
    )
    print(f"Wrote {len(odds)} standardized odds rows to {args.output}")
    print(f"Filtered outlier rows: {raw_row_count - len(odds)}")
    print(f"Raw snapshot: {raw_path}")
    if usage_headers:
        print(f"Usage: {usage_headers}")
    if unmatched:
        print(f"Unmatched events: {len(unmatched)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
