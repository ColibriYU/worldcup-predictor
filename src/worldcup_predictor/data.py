from __future__ import annotations

from pathlib import Path
import json

import pandas as pd

from .monitoring import filter_outlier_odds


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


def load_data(data_dir: Path = DATA_DIR) -> dict[str, pd.DataFrame]:
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
        "team_aliases": pd.read_csv(data_dir / "team_aliases.csv"),
        "odds_source": pd.DataFrame([{"source": odds_source}]),
        "odds_history": _read_optional_csv(data_dir / "odds_history.csv"),
        "odds_api_status": _read_optional_json_frame(data_dir / "odds_api_status.json"),
    }
