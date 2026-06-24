from __future__ import annotations

import numpy as np
import pandas as pd


def _clip_pct(value: float) -> float:
    return float(np.clip(value * 100, 0, 100))


def _score_probability(matrix: pd.DataFrame, predicate) -> float:
    total = 0.0
    for home_goals in matrix.index:
        for away_goals in matrix.columns:
            h = int(home_goals)
            a = int(away_goals)
            if predicate(h, a):
                total += float(matrix.loc[home_goals, away_goals])
    return total


def upset_index(
    *,
    home_team: str,
    away_team: str,
    final_probability: dict[str, float],
    odds_probability: dict[str, float],
    lambda_home: float,
    lambda_away: float,
) -> dict[str, object]:
    favorite = "home" if odds_probability["home"] >= odds_probability["away"] else "away"
    underdog = "away" if favorite == "home" else "home"
    favorite_team = home_team if favorite == "home" else away_team
    underdog_team = away_team if underdog == "away" else home_team

    underdog_win = float(final_probability[underdog])
    draw = float(final_probability["draw"])
    underdog_non_loss = underdog_win + draw
    favorite_non_win = underdog_non_loss
    total_goals = lambda_home + lambda_away
    low_score_factor = float(np.clip((2.9 - total_goals) / 2.9, 0, 1))
    model_market_gap = max(0.0, float(final_probability[underdog] - odds_probability[underdog]))
    favorite_doubt = max(0.0, float(odds_probability[favorite] - final_probability[favorite]))
    favorite_heat = float(
        np.clip((odds_probability[favorite] - 0.62) / 0.25, 0, 1)
        * np.clip(favorite_doubt * 4, 0, 1)
    )

    raw_score = (
        0.48 * underdog_non_loss
        + 0.08 * underdog_win
        + 0.15 * draw
        + 0.10 * low_score_factor
        + 0.10 * min(model_market_gap * 3, 1)
        + 0.12 * min(favorite_doubt * 3, 1)
        + 0.07 * favorite_heat
    )
    index = _clip_pct(raw_score)

    if index >= 52:
        level = "高"
    elif index >= 28:
        level = "中"
    else:
        level = "低"

    reasons = [
        f"{favorite_team}热门不胜概率 {favorite_non_win * 100:.1f}%",
        f"{underdog_team}直接赢球概率 {underdog_win * 100:.1f}%",
    ]
    if draw > 0.17:
        reasons.append(f"平局概率 {draw * 100:.1f}%，需要防热门被逼平")
    if low_score_factor > 0.25:
        reasons.append("预期总进球偏低，低比分会放大冷门/平局概率")
    if model_market_gap > 0.02:
        reasons.append("模型给弱队的概率高于市场去水概率")
    if favorite_doubt > 0.02:
        reasons.append("模型对热门方向比市场更谨慎")
    if favorite_heat > 0.20:
        reasons.append("市场对热门队定价偏热，存在被高估风险")

    return {
        "index": index,
        "level": level,
        "favorite": favorite,
        "favorite_team": favorite_team,
        "underdog": underdog,
        "underdog_team": underdog_team,
        "underdog_win_probability": underdog_win,
        "underdog_non_loss_probability": underdog_non_loss,
        "favorite_non_win_probability": favorite_non_win,
        "low_score_factor": low_score_factor,
        "model_market_gap": model_market_gap,
        "favorite_doubt": favorite_doubt,
        "favorite_heat": favorite_heat,
        "reasons": reasons,
    }


def big_score_index(
    *,
    score_matrix: pd.DataFrame,
    lambda_home: float,
    lambda_away: float,
    avg_over_under: float | None,
) -> dict[str, object]:
    over_2_5 = _score_probability(score_matrix, lambda h, a: h + a >= 3)
    over_3_5 = _score_probability(score_matrix, lambda h, a: h + a >= 4)
    over_4_5 = _score_probability(score_matrix, lambda h, a: h + a >= 5)
    both_score = _score_probability(score_matrix, lambda h, a: h > 0 and a > 0)
    big_margin = _score_probability(score_matrix, lambda h, a: abs(h - a) >= 3)
    total_goals = lambda_home + lambda_away
    line_factor = 0.0
    if avg_over_under and not np.isnan(avg_over_under):
        line_factor = float(np.clip((avg_over_under - 2.25) / 1.25, 0, 1))

    raw_score = (
        0.34 * over_2_5
        + 0.28 * over_3_5
        + 0.14 * over_4_5
        + 0.12 * both_score
        + 0.08 * big_margin
        + 0.04 * line_factor
    )
    index = _clip_pct(raw_score)

    if index >= 55:
        level = "高"
    elif index >= 35:
        level = "中"
    else:
        level = "低"

    reasons = [
        f"预期总进球 {total_goals:.2f}",
        f"Over 2.5 概率 {over_2_5 * 100:.1f}%",
        f"Over 3.5 概率 {over_3_5 * 100:.1f}%",
    ]
    if big_margin > 0.18:
        reasons.append("大胜比分区间概率较高")
    if both_score > 0.45:
        reasons.append("双方都有进球的概率较高")
    if avg_over_under and not np.isnan(avg_over_under):
        reasons.append(f"盘口大小球均线 {avg_over_under:.2f}")

    return {
        "index": index,
        "level": level,
        "over_2_5": over_2_5,
        "over_3_5": over_3_5,
        "over_4_5": over_4_5,
        "both_score": both_score,
        "big_margin": big_margin,
        "total_goals": total_goals,
        "reasons": reasons,
    }
