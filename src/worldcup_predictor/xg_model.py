from __future__ import annotations

import numpy as np
import pandas as pd

from .probability import OUTCOMES, normalize
from .score_model import score_matrix, score_outcome_probabilities


def _xg_row(xg_inputs: pd.DataFrame, match_id: str, team: str) -> pd.Series:
    rows = xg_inputs[
        (xg_inputs["match_id"] == match_id)
        & (xg_inputs["team"].str.casefold() == team.casefold())
    ]
    if rows.empty:
        raise ValueError(f"Missing xG inputs for {team} in {match_id}")
    return rows.iloc[0]


def quality_lambda(
    row: pd.Series,
    *,
    base_scale: float = 1.35,
    min_lambda: float = 0.05,
    max_lambda: float = 5.0,
) -> float:
    open_play = (
        base_scale
        * float(row["shot_quality"])
        * float(row["shot_location"])
        * (1 / max(float(row["defensive_pressure"]), 0.2))
        * float(row["transition_attack"])
        * float(row["tempo_factor"])
    )
    lam = open_play + float(row.get("set_piece_xg", 0.0))
    return min(max(lam, min_lambda), max_lambda)


def xg_lambdas(
    match_id: str,
    home_team: str,
    away_team: str,
    xg_inputs: pd.DataFrame,
    *,
    home_matchup_factor: float = 1.0,
    away_matchup_factor: float = 1.0,
    home_state_factor: float = 1.0,
    away_state_factor: float = 1.0,
) -> tuple[float, float]:
    home_row = _xg_row(xg_inputs, match_id, home_team)
    away_row = _xg_row(xg_inputs, match_id, away_team)
    lambda_home = quality_lambda(home_row) * home_matchup_factor * home_state_factor
    lambda_away = quality_lambda(away_row) * away_matchup_factor * away_state_factor
    return min(lambda_home, 5.0), min(lambda_away, 5.0)


def xg_probabilities(lambda_home: float, lambda_away: float, max_goals: int = 7) -> np.ndarray:
    matrix = score_matrix(lambda_home, lambda_away, max_goals=max_goals)
    outcomes = score_outcome_probabilities(matrix)
    return normalize([outcomes[outcome] for outcome in OUTCOMES])
