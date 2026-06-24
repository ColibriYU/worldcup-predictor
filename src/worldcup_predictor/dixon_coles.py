from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .probability import OUTCOMES, normalize, poisson_probability


def rho_factor(
    home_goals: int,
    away_goals: int,
    *,
    alpha: float = 0.13,
    beta: float = 0.9,
) -> float:
    total_goals = home_goals + away_goals
    return max(0.01, 1 - alpha * math.exp(-beta * total_goals))


def dixon_coles_matrix(
    lambda_home: float,
    lambda_away: float,
    *,
    max_goals: int = 7,
    alpha: float = 0.13,
    beta: float = 0.9,
) -> pd.DataFrame:
    values = np.zeros((max_goals + 1, max_goals + 1), dtype=float)
    for home_goals in range(max_goals + 1):
        for away_goals in range(max_goals + 1):
            base = poisson_probability(lambda_home, home_goals) * poisson_probability(
                lambda_away, away_goals
            )
            values[home_goals, away_goals] = base * rho_factor(
                home_goals,
                away_goals,
                alpha=alpha,
                beta=beta,
            )

    values = values / values.sum()
    return pd.DataFrame(
        values,
        index=[str(goals) for goals in range(max_goals + 1)],
        columns=[str(goals) for goals in range(max_goals + 1)],
    )


def matrix_outcome_probabilities(matrix: pd.DataFrame) -> np.ndarray:
    values = matrix.to_numpy()
    home = float(np.tril(values, k=-1).sum())
    draw = float(np.trace(values))
    away = float(np.triu(values, k=1).sum())
    return normalize([home, draw, away])


def dixon_coles_probabilities(
    lambda_home: float,
    lambda_away: float,
    *,
    max_goals: int = 7,
    alpha: float = 0.13,
    beta: float = 0.9,
) -> np.ndarray:
    matrix = dixon_coles_matrix(
        lambda_home,
        lambda_away,
        max_goals=max_goals,
        alpha=alpha,
        beta=beta,
    )
    return matrix_outcome_probabilities(matrix)


def dixon_coles_probability_dict(
    lambda_home: float,
    lambda_away: float,
    *,
    max_goals: int = 7,
    alpha: float = 0.13,
    beta: float = 0.9,
) -> dict[str, float]:
    return dict(
        zip(
            OUTCOMES,
            dixon_coles_probabilities(
                lambda_home,
                lambda_away,
                max_goals=max_goals,
                alpha=alpha,
                beta=beta,
            ),
        )
    )
