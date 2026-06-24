from __future__ import annotations

import pandas as pd


def bayesian_attack_defense(team_form: pd.DataFrame, team: str) -> tuple[float, float]:
    rows = team_form[team_form["team"].str.casefold() == team.casefold()]
    if rows.empty:
        return 1.0, 1.0
    row = rows.iloc[0]
    prior_matches = max(float(row["matches_played"]), 1.0)
    recent_matches = max(float(row["recent_matches"]), 1.0)
    attack = (
        float(row["prior_attack"]) * prior_matches + float(row["recent_xg_for"])
    ) / (prior_matches + recent_matches)
    defense = (
        float(row["prior_defense"]) * prior_matches + float(row["recent_xg_against"])
    ) / (prior_matches + recent_matches)
    form = float(row.get("form_multiplier", 1.0))
    return attack * form, defense


def bayesian_elo(
    team_stats: pd.DataFrame,
    past_results: pd.DataFrame,
    *,
    k_factor: float = 18.0,
) -> pd.DataFrame:
    updated = team_stats.copy()
    updated["bayesian_elo"] = updated["elo"].astype(float)

    def get_elo(team: str) -> float:
        return float(updated.loc[updated["team"] == team, "bayesian_elo"].iloc[0])

    def set_elo(team: str, value: float) -> None:
        updated.loc[updated["team"] == team, "bayesian_elo"] = value

    for _, match in past_results.iterrows():
        home = match["home_team"]
        away = match["away_team"]
        if home not in set(updated["team"]) or away not in set(updated["team"]):
            continue
        home_elo = get_elo(home)
        away_elo = get_elo(away)
        expected_home = 1 / (1 + 10 ** ((away_elo - home_elo) / 400))
        if int(match["home_goals"]) > int(match["away_goals"]):
            actual_home = 1.0
        elif int(match["home_goals"]) == int(match["away_goals"]):
            actual_home = 0.5
        else:
            actual_home = 0.0

        xg_margin = float(match["home_xg"]) - float(match["away_xg"])
        confidence = min(1.5, max(0.6, 1 + abs(xg_margin) / 3))
        delta = k_factor * confidence * (actual_home - expected_home)
        set_elo(home, home_elo + delta)
        set_elo(away, away_elo - delta)

    return updated


def state_factor(team_form: pd.DataFrame, team: str, *, league_avg_attack: float = 1.6) -> float:
    attack, _ = bayesian_attack_defense(team_form, team)
    return max(0.75, min(1.25, attack / league_avg_attack))
