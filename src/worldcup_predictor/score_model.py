from __future__ import annotations

import numpy as np
import pandas as pd

from .probability import OUTCOMES, normalize, poisson_probability


def expected_goals(
    attack_home: float,
    defense_away: float,
    attack_away: float,
    defense_home: float,
    *,
    max_lambda: float = 5.0,
) -> tuple[float, float]:
    lambda_home = min(max(attack_home * defense_away, 0.05), max_lambda)
    lambda_away = min(max(attack_away * defense_home, 0.05), max_lambda)
    return lambda_home, lambda_away


def score_matrix(lambda_home: float, lambda_away: float, max_goals: int = 7) -> pd.DataFrame:
    home_probs = [poisson_probability(lambda_home, goals) for goals in range(max_goals + 1)]
    away_probs = [poisson_probability(lambda_away, goals) for goals in range(max_goals + 1)]
    matrix = np.outer(home_probs, away_probs)
    return pd.DataFrame(
        matrix,
        index=[str(goals) for goals in range(max_goals + 1)],
        columns=[str(goals) for goals in range(max_goals + 1)],
    )


def score_outcome_probabilities(matrix: pd.DataFrame) -> dict[str, float]:
    values = matrix.to_numpy()
    home = float(np.tril(values, k=-1).sum())
    draw = float(np.trace(values))
    away = float(np.triu(values, k=1).sum())
    home, draw, away = normalize([home, draw, away])
    return dict(zip(OUTCOMES, [home, draw, away]))


def top_scores(matrix: pd.DataFrame, limit: int = 6) -> pd.DataFrame:
    rows = []
    for home_goals in matrix.index:
        for away_goals in matrix.columns:
            rows.append(
                {
                    "score": f"{home_goals}-{away_goals}",
                    "home_goals": int(home_goals),
                    "away_goals": int(away_goals),
                    "probability": float(matrix.loc[home_goals, away_goals]),
                }
            )
    result = pd.DataFrame(rows).sort_values("probability", ascending=False).head(limit)
    result["probability_pct"] = result["probability"] * 100
    return result.reset_index(drop=True)
