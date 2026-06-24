from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import re
import unicodedata
from typing import Any

import pandas as pd
import requests


BASE_URL = "https://api.the-odds-api.com/v4"
DEFAULT_SPORT = "soccer_fifa_world_cup"
DEFAULT_REGIONS = "eu"
DEFAULT_MARKETS = "h2h,spreads,totals"


@dataclass(frozen=True)
class OddsApiConfig:
    api_key: str
    sport: str = DEFAULT_SPORT
    regions: str = DEFAULT_REGIONS
    markets: str = DEFAULT_MARKETS
    odds_format: str = "decimal"
    date_format: str = "iso"
    bookmakers: str | None = None
    timeout_seconds: int = 20


def fetch_odds(config: OddsApiConfig) -> tuple[list[dict[str, Any]], dict[str, str]]:
    url = f"{BASE_URL}/sports/{config.sport}/odds"
    params: dict[str, str] = {
        "apiKey": config.api_key,
        "regions": config.regions,
        "markets": config.markets,
        "oddsFormat": config.odds_format,
        "dateFormat": config.date_format,
    }
    if config.bookmakers:
        params["bookmakers"] = config.bookmakers

    response = requests.get(url, params=params, timeout=config.timeout_seconds)
    response.raise_for_status()
    usage_headers = {
        key: value
        for key, value in response.headers.items()
        if key.lower().startswith("x-requests")
    }
    return response.json(), usage_headers


def write_raw_snapshot(events: list[dict[str, Any]], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = output_dir / f"the_odds_api_{stamp}.json"
    path.write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_status(
    path: Path,
    *,
    rows: int,
    raw_path: Path,
    config: OddsApiConfig,
    usage_headers: dict[str, str],
    unmatched_events: list[dict[str, str]],
) -> None:
    status = {
        "provider": "the_odds_api",
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "sport": config.sport,
        "regions": config.regions,
        "markets": config.markets,
        "rows": rows,
        "raw_path": str(raw_path),
        "usage_headers": usage_headers,
        "unmatched_events": unmatched_events,
    }
    path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_name(value: str) -> str:
    ascii_value = (
        unicodedata.normalize("NFKD", value.replace("&", " and "))
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    return re.sub(r"[^a-z0-9]+", "", ascii_value.casefold())


def build_alias_map(team_aliases: pd.DataFrame | None, teams: pd.Series) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for team in teams.dropna().unique():
        aliases[normalize_name(str(team))] = str(team)

    if team_aliases is not None and not team_aliases.empty:
        for _, row in team_aliases.iterrows():
            aliases[normalize_name(str(row["alias"]))] = str(row["internal_team"])
    return aliases


def resolve_team(name: str, alias_map: dict[str, str]) -> str | None:
    return alias_map.get(normalize_name(name))


def _market(bookmaker: dict[str, Any], key: str) -> dict[str, Any] | None:
    for market in bookmaker.get("markets", []):
        if market.get("key") == key:
            return market
    return None


def _outcome_price(
    market: dict[str, Any] | None,
    internal_team: str,
    alias_map: dict[str, str],
) -> float | None:
    if market is None:
        return None
    for outcome in market.get("outcomes", []):
        resolved = resolve_team(str(outcome.get("name", "")), alias_map)
        if resolved == internal_team:
            return float(outcome["price"])
    return None


def _draw_price(market: dict[str, Any] | None) -> float | None:
    if market is None:
        return None
    for outcome in market.get("outcomes", []):
        if str(outcome.get("name", "")).casefold() == "draw":
            return float(outcome["price"])
    return None


def _totals_line(market: dict[str, Any] | None) -> tuple[float | None, float | None, float | None]:
    if market is None:
        return None, None, None
    over_line = over_price = under_price = None
    for outcome in market.get("outcomes", []):
        name = str(outcome.get("name", "")).casefold()
        if name == "over":
            over_line = float(outcome["point"])
            over_price = float(outcome["price"])
        elif name == "under":
            under_price = float(outcome["price"])
    return over_line, over_price, under_price


def _spread_values(
    market: dict[str, Any] | None,
    home_team: str,
    away_team: str,
    alias_map: dict[str, str],
) -> tuple[float | None, float | None, float | None, float | None]:
    if market is None:
        return None, None, None, None
    home_point = home_price = away_point = away_price = None
    for outcome in market.get("outcomes", []):
        resolved = resolve_team(str(outcome.get("name", "")), alias_map)
        if resolved == home_team:
            home_point = float(outcome["point"])
            home_price = float(outcome["price"])
        elif resolved == away_team:
            away_point = float(outcome["point"])
            away_price = float(outcome["price"])
    return home_point, home_price, away_point, away_price


def _previous_open(
    previous_odds: pd.DataFrame | None,
    match_id: str,
    bookmaker: str,
    current: tuple[float, float, float],
) -> tuple[float, float, float]:
    if previous_odds is None or previous_odds.empty:
        return current
    rows = previous_odds[
        (previous_odds["match_id"] == match_id) & (previous_odds["bookmaker"] == bookmaker)
    ]
    if rows.empty:
        return current
    row = rows.iloc[0]
    return (
        float(row.get("open_home", current[0])),
        float(row.get("open_draw", current[1])),
        float(row.get("open_away", current[2])),
    )


def _match_id_for_event(
    home_team: str,
    away_team: str,
    matches: pd.DataFrame,
) -> str | None:
    rows = matches[
        (matches["home_team"] == home_team) & (matches["away_team"] == away_team)
    ]
    if rows.empty:
        rows = matches[
            (matches["home_team"] == away_team) & (matches["away_team"] == home_team)
        ]
    if rows.empty:
        return None
    return str(rows.iloc[0]["match_id"])


def _team_code(team: str) -> str:
    normalized = normalize_name(team).upper()
    return normalized[:3] if normalized else "TEAM"


def _generated_match_id(event: dict[str, Any], home_team: str, away_team: str) -> str:
    event_id = normalize_name(str(event.get("id") or "")).upper()
    suffix = event_id[:8] if event_id else "API"
    return f"{_team_code(home_team)}-{_team_code(away_team)}-{suffix}"


def normalize_odds_response(
    events: list[dict[str, Any]],
    matches: pd.DataFrame,
    team_aliases: pd.DataFrame | None = None,
    previous_odds: pd.DataFrame | None = None,
    include_unlisted_events: bool = False,
) -> tuple[pd.DataFrame, list[dict[str, str]]]:
    teams = pd.concat([matches["home_team"], matches["away_team"]], ignore_index=True)
    alias_map = build_alias_map(team_aliases, teams)
    rows: list[dict[str, Any]] = []
    unmatched_events: list[dict[str, str]] = []

    for event in events:
        api_home = str(event.get("home_team", ""))
        api_away = str(event.get("away_team", ""))
        resolved_home = resolve_team(api_home, alias_map)
        resolved_away = resolve_team(api_away, alias_map)
        if include_unlisted_events:
            if not resolved_home:
                resolved_home = api_home
                alias_map[normalize_name(api_home)] = resolved_home
            if not resolved_away:
                resolved_away = api_away
                alias_map[normalize_name(api_away)] = resolved_away
        if not resolved_home or not resolved_away:
            unmatched_events.append(
                {"home_team": api_home, "away_team": api_away, "reason": "team_alias"}
            )
            continue

        match_id = _match_id_for_event(resolved_home, resolved_away, matches)
        if not match_id:
            if not include_unlisted_events:
                unmatched_events.append(
                    {"home_team": api_home, "away_team": api_away, "reason": "match_id"}
                )
                continue
            match_id = _generated_match_id(event, resolved_home, resolved_away)
            model_home = resolved_home
            model_away = resolved_away
        else:
            match_row = matches[matches["match_id"] == match_id].iloc[0]
            model_home = str(match_row["home_team"])
            model_away = str(match_row["away_team"])

        for bookmaker in event.get("bookmakers", []):
            bookmaker_name = str(bookmaker.get("title") or bookmaker.get("key"))
            h2h = _market(bookmaker, "h2h")
            home_odds = _outcome_price(h2h, model_home, alias_map)
            away_odds = _outcome_price(h2h, model_away, alias_map)
            draw_odds = _draw_price(h2h)
            if home_odds is None or draw_odds is None or away_odds is None:
                continue

            open_home, open_draw, open_away = _previous_open(
                previous_odds,
                match_id,
                bookmaker_name,
                (home_odds, draw_odds, away_odds),
            )
            total_line, over_price, under_price = _totals_line(_market(bookmaker, "totals"))
            spread_home, spread_home_price, spread_away, spread_away_price = _spread_values(
                _market(bookmaker, "spreads"),
                model_home,
                model_away,
                alias_map,
            )

            rows.append(
                {
                    "match_id": match_id,
                    "bookmaker": bookmaker_name,
                    "open_home": open_home,
                    "open_draw": open_draw,
                    "open_away": open_away,
                    "home_odds": home_odds,
                    "draw_odds": draw_odds,
                    "away_odds": away_odds,
                    "over_under_line": total_line,
                    "over_price": over_price,
                    "under_price": under_price,
                    "spread_home": spread_home,
                    "spread_home_price": spread_home_price,
                    "spread_away": spread_away,
                    "spread_away_price": spread_away_price,
                    "provider": "the_odds_api",
                    "event_id": event.get("id"),
                    "commence_time": event.get("commence_time"),
                    "last_update": bookmaker.get("last_update"),
                }
            )

    odds = pd.DataFrame(rows)
    if odds.empty:
        return odds, unmatched_events
    return odds.sort_values(["match_id", "bookmaker"]).reset_index(drop=True), unmatched_events
