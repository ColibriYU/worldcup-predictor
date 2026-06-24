from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd

from .probability import OUTCOMES, odds_to_probabilities


ODDS_COLUMNS = ["home_odds", "draw_odds", "away_odds"]
OUTCOME_LABELS = {"home": "主胜", "draw": "平局", "away": "客胜"}


def filter_outlier_odds(
    odds: pd.DataFrame,
    *,
    max_median_ratio: float = 2.2,
    min_median_ratio: float = 0.45,
) -> pd.DataFrame:
    """Remove bookmaker rows far away from match-level consensus."""
    if odds.empty:
        return odds

    frames = []
    for _, group in odds.groupby("match_id", dropna=False):
        if len(group) < 4:
            frames.append(group)
            continue
        keep = pd.Series(True, index=group.index)
        for column in ODDS_COLUMNS:
            median = float(group[column].median())
            if median <= 0:
                continue
            ratio = group[column].astype(float) / median
            keep &= ratio.between(min_median_ratio, max_median_ratio)
        frames.append(group[keep])

    if not frames:
        return odds.iloc[0:0].copy()
    return pd.concat(frames, ignore_index=True)


def append_odds_history(
    odds: pd.DataFrame,
    history_path: Path,
    *,
    fetched_at: str | None = None,
) -> None:
    if odds.empty:
        return
    snapshot = odds.copy()
    snapshot["fetched_at"] = fetched_at or datetime.now(timezone.utc).isoformat()
    history_path.parent.mkdir(parents=True, exist_ok=True)

    if history_path.exists():
        previous = pd.read_csv(history_path)
        combined = pd.concat([previous, snapshot], ignore_index=True)
    else:
        combined = snapshot

    combined.to_csv(history_path, index=False, encoding="utf-8")


def odds_change_summary(
    history: pd.DataFrame,
    *,
    min_abs_move_pct: float = 3.0,
) -> pd.DataFrame:
    if history.empty or "fetched_at" not in history.columns:
        return pd.DataFrame()

    history = filter_outlier_odds(history)
    rows = []
    grouped = history.sort_values("fetched_at").groupby(["match_id", "bookmaker"], dropna=False)
    for (match_id, bookmaker), group in grouped:
        if len(group) < 2:
            continue
        first = group.iloc[0]
        latest = group.iloc[-1]
        for column, outcome in zip(ODDS_COLUMNS, OUTCOMES):
            old = float(first[column])
            new = float(latest[column])
            if old <= 0:
                continue
            move_pct = (new - old) / old * 100
            if abs(move_pct) < min_abs_move_pct:
                continue
            rows.append(
                {
                    "match_id": match_id,
                    "bookmaker": bookmaker,
                    "outcome": outcome,
                    "outcome_label": OUTCOME_LABELS[outcome],
                    "old_odds": old,
                    "new_odds": new,
                    "move_pct": move_pct,
                    "direction": "赔率上升" if move_pct > 0 else "赔率下降",
                    "first_seen": first["fetched_at"],
                    "latest_seen": latest["fetched_at"],
                }
            )

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("move_pct", key=lambda col: col.abs(), ascending=False)


def bookmaker_value_bets(
    match_odds: pd.DataFrame,
    model_probabilities: dict[str, float],
    *,
    min_edge: float = 0.03,
    min_model_probability: float = 0.05,
) -> pd.DataFrame:
    match_odds = filter_outlier_odds(match_odds)
    rows = []
    for _, odds_row in match_odds.iterrows():
        market_probs = odds_to_probabilities(odds_row)
        for idx, outcome in enumerate(OUTCOMES):
            model_probability = float(model_probabilities[outcome])
            if model_probability < min_model_probability:
                continue
            odds_value = float(odds_row[ODDS_COLUMNS[idx]])
            fair_odds = 1 / model_probability
            edge = model_probability * odds_value - 1
            probability_gap = model_probability - float(market_probs[idx])
            if edge < min_edge:
                continue
            rows.append(
                {
                    "match_id": odds_row["match_id"],
                    "bookmaker": odds_row["bookmaker"],
                    "outcome": outcome,
                    "outcome_label": OUTCOME_LABELS[outcome],
                    "odds": odds_value,
                    "model_probability": model_probability,
                    "market_probability": float(market_probs[idx]),
                    "probability_gap": probability_gap,
                    "fair_odds": fair_odds,
                    "edge": edge,
                    "edge_pct": edge * 100,
                }
            )

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(["edge", "probability_gap"], ascending=False)


def combined_value_bets(
    odds: pd.DataFrame,
    predictions: Iterable[dict[str, object]],
    *,
    min_edge: float = 0.03,
) -> pd.DataFrame:
    frames = []
    for prediction in predictions:
        match_id = str(prediction["match_id"])
        match_odds = odds[odds["match_id"] == match_id]
        if match_odds.empty:
            continue
        frame = bookmaker_value_bets(
            match_odds,
            prediction["final_probability"],
            min_edge=min_edge,
        )
        if frame.empty:
            continue
        frame["match"] = f"{prediction['home_team']} vs {prediction['away_team']}"
        frames.append(frame)

    if not frames:
        return pd.DataFrame()
    result = pd.concat(frames, ignore_index=True)
    return result.sort_values("edge", ascending=False).reset_index(drop=True)
