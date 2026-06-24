from __future__ import annotations

import math
from typing import Iterable

import numpy as np
import pandas as pd

OUTCOMES = ("home", "draw", "away")


def normalize(values: Iterable[float]) -> np.ndarray:
    arr = np.asarray(list(values), dtype=float)
    arr = np.clip(arr, 0.0, None)
    total = arr.sum()
    if total <= 0:
        return np.repeat(1 / len(arr), len(arr))
    return arr / total


def odds_to_probabilities(odds_row: pd.Series, prefix: str = "") -> np.ndarray:
    odds = [
        float(odds_row[f"{prefix}home_odds"] if prefix else odds_row["home_odds"]),
        float(odds_row[f"{prefix}draw_odds"] if prefix else odds_row["draw_odds"]),
        float(odds_row[f"{prefix}away_odds"] if prefix else odds_row["away_odds"]),
    ]
    implied = [1 / value for value in odds]
    return normalize(implied)


def aggregate_odds_probabilities(match_odds: pd.DataFrame) -> np.ndarray:
    probabilities = [odds_to_probabilities(row) for _, row in match_odds.iterrows()]
    return normalize(np.mean(probabilities, axis=0))


def market_bias(match_odds: pd.DataFrame) -> np.ndarray:
    """Return market movement from opening odds to current odds by outcome.

    Positive value means the current market is assigning more probability than the
    opening market did after removing bookmaker margin.
    """
    deltas = []
    renamed = match_odds.rename(
        columns={
            "open_home": "open_home_odds",
            "open_draw": "open_draw_odds",
            "open_away": "open_away_odds",
        }
    )
    for _, row in renamed.iterrows():
        opening = odds_to_probabilities(row, prefix="open_")
        current = odds_to_probabilities(row)
        deltas.append(current - opening)
    if not deltas:
        return np.zeros(3)
    return np.mean(deltas, axis=0)


def elo_probabilities(
    home_elo: float,
    away_elo: float,
    *,
    draw_base: float = 0.26,
    draw_decay: float = 0.12,
    home_advantage: float = 0.0,
) -> np.ndarray:
    elo_gap = (home_elo + home_advantage) - away_elo
    home_binary = 1 / (1 + 10 ** (-elo_gap / 400))
    draw_probability = draw_base - draw_decay * min(abs(elo_gap), 500) / 500
    draw_probability = min(max(draw_probability, 0.12), 0.32)
    non_draw = 1 - draw_probability
    return normalize(
        [
            non_draw * home_binary,
            draw_probability,
            non_draw * (1 - home_binary),
        ]
    )


def apply_market_adjustment(
    probabilities: Iterable[float],
    bias: Iterable[float],
    *,
    k: float,
) -> np.ndarray:
    base = np.asarray(list(probabilities), dtype=float)
    bias_values = np.asarray(list(bias), dtype=float)
    adjusted = base * (1 + k * bias_values)
    return normalize(adjusted)


def poisson_probability(lam: float, goals: int) -> float:
    return (lam**goals * math.exp(-lam)) / math.factorial(goals)
