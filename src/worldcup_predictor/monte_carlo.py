from __future__ import annotations

import numpy as np
import pandas as pd

from .dixon_coles import rho_factor
from .probability import OUTCOMES, normalize


def simulate_match(
    lambda_home: float,
    lambda_away: float,
    *,
    simulations: int = 10000,
    alpha: float = 0.13,
    beta: float = 0.9,
    seed: int = 42,
    max_goals: int = 10,
) -> dict[str, object]:
    rng = np.random.default_rng(seed)
    home_goals = np.clip(rng.poisson(lambda_home, simulations), 0, max_goals)
    away_goals = np.clip(rng.poisson(lambda_away, simulations), 0, max_goals)

    weights = np.array(
        [
            rho_factor(int(home), int(away), alpha=alpha, beta=beta)
            for home, away in zip(home_goals, away_goals)
        ],
        dtype=float,
    )
    weights = weights / weights.sum()

    home_win = float(weights[home_goals > away_goals].sum())
    draw = float(weights[home_goals == away_goals].sum())
    away_win = float(weights[home_goals < away_goals].sum())
    probabilities = normalize([home_win, draw, away_win])

    score_labels = np.array([f"{home}-{away}" for home, away in zip(home_goals, away_goals)])
    score_frame = pd.DataFrame({"score": score_labels, "weight": weights})
    top_scores = (
        score_frame.groupby("score", as_index=False)["weight"]
        .sum()
        .sort_values("weight", ascending=False)
        .head(8)
        .rename(columns={"weight": "probability"})
        .reset_index(drop=True)
    )
    top_scores["probability_pct"] = top_scores["probability"] * 100

    return {
        "probabilities": dict(zip(OUTCOMES, probabilities)),
        "top_scores": top_scores,
        "simulations": simulations,
    }
