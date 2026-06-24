from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd

from .monitoring import append_odds_history, filter_outlier_odds
from .odds_api import (
    DEFAULT_MARKETS,
    DEFAULT_REGIONS,
    DEFAULT_SPORT,
    OddsApiConfig,
    fetch_odds,
    normalize_odds_response,
    write_raw_snapshot,
    write_status,
)


DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _load_odds(data_dir: Path) -> tuple[pd.DataFrame, str]:
    live_path = data_dir / "odds_live.csv"
    fallback = pd.read_csv(data_dir / "odds.csv")
    if live_path.exists():
        live = pd.read_csv(live_path)
        if not live.empty:
            live = filter_outlier_odds(live)
            missing_match_ids = set(fallback["match_id"]) - set(live["match_id"])
            if missing_match_ids:
                fallback_rows = fallback[fallback["match_id"].isin(missing_match_ids)]
                merged = pd.concat([live, fallback_rows], ignore_index=True)
                return merged, "odds_live.csv + odds.csv fallback"
            return live, "odds_live.csv"
    return fallback, "odds.csv"


def _read_optional_csv(path: Path) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def _read_optional_json_frame(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.DataFrame([json.loads(path.read_text(encoding="utf-8"))])


def _write_error_status(
    path: Path,
    *,
    sport: str,
    regions: str,
    markets: str,
    error: Exception,
) -> None:
    status = {
        "provider": "the_odds_api",
        "fetched_at_utc": pd.Timestamp.utcnow().isoformat(),
        "sport": sport,
        "regions": regions,
        "markets": markets,
        "rows": 0,
        "raw_path": "",
        "usage_headers": {},
        "unmatched_events": [],
        "error": str(error),
    }
    path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")


def update_live_odds(
    *,
    api_key: str,
    data_dir: Path = DATA_DIR,
    sport: str = DEFAULT_SPORT,
    regions: str = DEFAULT_REGIONS,
    markets: str = DEFAULT_MARKETS,
    bookmakers: str | None = None,
) -> None:
    matches = pd.read_csv(data_dir / "matches.csv")
    team_aliases = pd.read_csv(data_dir / "team_aliases.csv")
    output_path = data_dir / "odds_live.csv"
    previous_path = output_path if output_path.exists() else data_dir / "odds.csv"
    previous_odds = pd.read_csv(previous_path) if previous_path.exists() else pd.DataFrame()
    config = OddsApiConfig(
        api_key=api_key,
        sport=sport,
        regions=regions,
        markets=markets,
        bookmakers=bookmakers,
    )

    try:
        events, usage_headers = fetch_odds(config)
        raw_path = write_raw_snapshot(events, data_dir / "odds_raw")
        odds, unmatched = normalize_odds_response(
            events,
            matches,
            team_aliases=team_aliases,
            previous_odds=previous_odds,
            include_unlisted_events=True,
        )
        odds = filter_outlier_odds(odds)
        if odds.empty:
            write_status(
                data_dir / "odds_api_status.json",
                rows=0,
                raw_path=raw_path,
                config=config,
                usage_headers=usage_headers,
                unmatched_events=unmatched,
            )
            return

        output_path.parent.mkdir(parents=True, exist_ok=True)
        odds.to_csv(output_path, index=False, encoding="utf-8")
        append_odds_history(odds, data_dir / "odds_history.csv")
        write_status(
            data_dir / "odds_api_status.json",
            rows=len(odds),
            raw_path=raw_path,
            config=config,
            usage_headers=usage_headers,
            unmatched_events=unmatched,
        )
    except Exception as exc:
        _write_error_status(
            data_dir / "odds_api_status.json",
            sport=sport,
            regions=regions,
            markets=markets,
            error=exc,
        )


def load_data(data_dir: Path = DATA_DIR, *, api_key: str | None = None) -> dict[str, pd.DataFrame]:
    api_key = api_key or os.getenv("THE_ODDS_API_KEY")
    if api_key:
        update_live_odds(api_key=api_key, data_dir=data_dir)

    matches = pd.read_csv(data_dir / "matches.csv")
    matches["neutral_site"] = matches["neutral_site"].astype(bool)
    odds, odds_source = _load_odds(data_dir)
    return {
        "matches": matches,
        "team_stats": pd.read_csv(data_dir / "team_stats.csv"),
        "odds": odds,
        "factors": pd.read_csv(data_dir / "factors.csv"),
        "external_predictions": pd.read_csv(data_dir / "external_predictions.csv"),
        "xg_inputs": pd.read_csv(data_dir / "xg_inputs.csv"),
        "team_form": pd.read_csv(data_dir / "team_form.csv"),
        "matchup_factors": pd.read_csv(data_dir / "matchup_factors.csv"),
        "past_results": pd.read_csv(data_dir / "past_results.csv"),
        "worldcup_schedule": pd.read_csv(data_dir / "worldcup_schedule.csv"),
        "group_standings": _read_optional_csv(data_dir / "group_standings.csv"),
        "knockout_paths": _read_optional_csv(data_dir / "knockout_paths.csv"),
        "team_aliases": pd.read_csv(data_dir / "team_aliases.csv"),
        "odds_source": pd.DataFrame([{"source": odds_source}]),
        "odds_history": _read_optional_csv(data_dir / "odds_history.csv"),
        "odds_api_status": _read_optional_json_frame(data_dir / "odds_api_status.json"),
    }
