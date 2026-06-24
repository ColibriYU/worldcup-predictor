from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .bayesian import bayesian_elo, state_factor
from .dixon_coles import dixon_coles_matrix, dixon_coles_probabilities
from .external import aggregate_external_predictions
from .group_context import group_stage_factors, knockout_context
from .indices import big_score_index, upset_index
from .market_flow import market_flow_flags, market_flow_probabilities
from .monte_carlo import simulate_match
from .probability import (
    OUTCOMES,
    aggregate_odds_probabilities,
    apply_market_adjustment,
    elo_probabilities,
    market_bias,
    normalize,
)
from .score_model import expected_goals, top_scores
from .xg_model import xg_lambdas, xg_probabilities


@dataclass(frozen=True)
class PredictionConfig:
    elo_weight: float = 0.22
    odds_weight: float = 0.30
    external_weight: float = 0.16
    xg_weight: float = 0.22
    market_flow_weight: float = 0.10
    market_bias_k: float = 2.0
    draw_base: float = 0.26
    draw_decay: float = 0.12
    home_advantage: float = 0.0
    max_goals: int = 7
    dc_alpha: float = 0.13
    dc_beta: float = 0.9
    simulations: int = 10000


def _team_row(team_stats: pd.DataFrame, team: str) -> pd.Series:
    matches = team_stats[team_stats["team"].str.casefold() == team.casefold()]
    if matches.empty:
        raise ValueError(f"Missing team stats for {team}")
    return matches.iloc[0]


def predict_match(
    match: pd.Series,
    team_stats: pd.DataFrame,
    odds: pd.DataFrame,
    factors: pd.DataFrame | None = None,
    external_predictions: pd.DataFrame | None = None,
    xg_inputs: pd.DataFrame | None = None,
    team_form: pd.DataFrame | None = None,
    matchup_factors: pd.DataFrame | None = None,
    past_results: pd.DataFrame | None = None,
    group_standings: pd.DataFrame | None = None,
    knockout_paths: pd.DataFrame | None = None,
    config: PredictionConfig | None = None,
    odds_source: str = "odds.csv",
) -> dict[str, object]:
    config = config or PredictionConfig()
    match_id = match["match_id"]
    home_team = match["home_team"]
    away_team = match["away_team"]

    elo_source = (
        bayesian_elo(team_stats, past_results)
        if past_results is not None and not past_results.empty
        else team_stats.assign(bayesian_elo=team_stats["elo"].astype(float))
    )
    home = _team_row(elo_source, home_team)
    away = _team_row(elo_source, away_team)
    match_odds = odds[odds["match_id"] == match_id]
    if match_odds.empty:
        raise ValueError(f"Missing odds for match {match_id}")

    odds_probability = aggregate_odds_probabilities(match_odds)
    elo_probability = elo_probabilities(
        float(home["elo"]),
        float(away["elo"]),
        draw_base=config.draw_base,
        draw_decay=config.draw_decay,
        home_advantage=0 if bool(match.get("neutral_site", True)) else config.home_advantage,
    )

    bias = market_bias(match_odds)
    market_probability = market_flow_probabilities(match_odds)

    if external_predictions is not None and not external_predictions.empty:
        match_external = external_predictions[external_predictions["match_id"] == match_id]
        external_probability = aggregate_external_predictions(match_external)
    else:
        match_external = pd.DataFrame()
        external_probability = np.repeat(1 / 3, 3)

    matchup = pd.Series(
        {
            "home_matchup_factor": 1.0,
            "away_matchup_factor": 1.0,
            "summary": "暂无战术克制数据",
        }
    )
    if matchup_factors is not None and not matchup_factors.empty:
        rows = matchup_factors[matchup_factors["match_id"] == match_id]
        if not rows.empty:
            matchup = rows.iloc[0]

    home_state = state_factor(team_form, home_team) if team_form is not None else 1.0
    away_state = state_factor(team_form, away_team) if team_form is not None else 1.0

    if xg_inputs is not None and not xg_inputs.empty:
        lambda_home, lambda_away = xg_lambdas(
            match_id,
            home_team,
            away_team,
            xg_inputs,
            home_matchup_factor=float(matchup["home_matchup_factor"]),
            away_matchup_factor=float(matchup["away_matchup_factor"]),
            home_state_factor=home_state,
            away_state_factor=away_state,
        )
        xg_probability = xg_probabilities(lambda_home, lambda_away, config.max_goals)
    else:
        raw_home = _team_row(team_stats, home_team)
        raw_away = _team_row(team_stats, away_team)
        lambda_home, lambda_away = expected_goals(
            float(raw_home["attack_strength"]),
            float(raw_away["defense_factor"]),
            float(raw_away["attack_strength"]),
            float(raw_home["defense_factor"]),
        )
        xg_probability = dixon_coles_probabilities(lambda_home, lambda_away)

    weights = np.asarray(
        [
            config.elo_weight,
            config.odds_weight,
            config.external_weight,
            config.xg_weight,
            config.market_flow_weight,
        ],
        dtype=float,
    )
    weights = normalize(weights)
    base_probability = normalize(
        weights[0] * elo_probability
        + weights[1] * odds_probability
        + weights[2] * external_probability
        + weights[3] * xg_probability
        + weights[4] * market_probability
    )

    market_adjusted_probability = apply_market_adjustment(base_probability, bias, k=config.market_bias_k)

    group_context = knockout_context(
        match,
        group_standings,
        knockout_paths,
        team_stats,
    )
    final_probability = normalize(
        market_adjusted_probability + np.asarray(group_context["probability_delta"], dtype=float)
    )

    lambda_multiplier = group_context["lambda_multiplier"]
    lambda_home = float(lambda_home * lambda_multiplier["home"])
    lambda_away = float(lambda_away * lambda_multiplier["away"])

    matrix = dixon_coles_matrix(
        lambda_home,
        lambda_away,
        max_goals=config.max_goals,
        alpha=config.dc_alpha,
        beta=config.dc_beta,
    )
    top = top_scores(matrix)
    score_probability = dict(
        zip(
            OUTCOMES,
            dixon_coles_probabilities(
                lambda_home,
                lambda_away,
                max_goals=config.max_goals,
                alpha=config.dc_alpha,
                beta=config.dc_beta,
            ),
        )
    )
    simulation = simulate_match(
        lambda_home,
        lambda_away,
        simulations=config.simulations,
        alpha=config.dc_alpha,
        beta=config.dc_beta,
        seed=abs(hash(match_id)) % (2**32),
    )

    match_factors = pd.DataFrame()
    if factors is not None and not factors.empty:
        match_factors = factors[factors["match_id"] == match_id].copy()
    if group_standings is not None and not group_standings.empty:
        fixture_context = pd.DataFrame(
            [
                {
                    "match_id": match_id,
                    "group": match["group"],
                    "home_team": home_team,
                    "away_team": away_team,
                }
            ]
        )
        group_factors = group_stage_factors(fixture_context, group_standings)
        if not group_factors.empty:
            match_factors = pd.concat([match_factors, group_factors], ignore_index=True)

    avg_over_under = float(np.nanmean(match_odds["over_under_line"]))
    upset = upset_index(
        home_team=home_team,
        away_team=away_team,
        final_probability=dict(zip(OUTCOMES, final_probability)),
        odds_probability=dict(zip(OUTCOMES, odds_probability)),
        lambda_home=lambda_home,
        lambda_away=lambda_away,
    )
    big_score = big_score_index(
        score_matrix=matrix,
        lambda_home=lambda_home,
        lambda_away=lambda_away,
        avg_over_under=avg_over_under,
    )

    return {
        "match_id": match_id,
        "home_team": home_team,
        "away_team": away_team,
        "odds_probability": dict(zip(OUTCOMES, odds_probability)),
        "elo_probability": dict(zip(OUTCOMES, elo_probability)),
        "external_probability": dict(zip(OUTCOMES, external_probability)),
        "xg_probability": dict(zip(OUTCOMES, xg_probability)),
        "market_flow_probability": dict(zip(OUTCOMES, market_probability)),
        "base_probability": dict(zip(OUTCOMES, base_probability)),
        "market_bias": dict(zip(OUTCOMES, bias)),
        "market_adjusted_probability": dict(zip(OUTCOMES, market_adjusted_probability)),
        "final_probability": dict(zip(OUTCOMES, final_probability)),
        "lambda_home": lambda_home,
        "lambda_away": lambda_away,
        "score_matrix": matrix,
        "score_outcomes": score_probability,
        "top_scores": top,
        "monte_carlo": simulation,
        "factors": match_factors,
        "external_sources": match_external,
        "market_flow_flags": market_flow_flags(match_odds, is_live=odds_source == "odds_live.csv"),
        "matchup_summary": str(matchup["summary"]),
        "bayesian_elo": {
            "home": float(home["bayesian_elo"]),
            "away": float(away["bayesian_elo"]),
        },
        "state_factor": {
            "home": home_state,
            "away": away_state,
        },
        "upset": upset,
        "big_score": big_score,
        "group_context": group_context,
        "layer_weights": dict(
            zip(
                ["elo", "odds", "external", "xg", "market_flow"],
                weights,
            )
        ),
        "bookmaker_count": int(match_odds["bookmaker"].nunique()),
        "avg_over_under": avg_over_under,
    }
