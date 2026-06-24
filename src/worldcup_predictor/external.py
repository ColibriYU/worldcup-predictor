from __future__ import annotations

import numpy as np
import pandas as pd

from .probability import OUTCOMES, normalize


def aggregate_external_predictions(predictions: pd.DataFrame) -> np.ndarray:
    if predictions.empty:
        return np.repeat(1 / 3, 3)

    values = predictions[["home_probability", "draw_probability", "away_probability"]].to_numpy(
        dtype=float
    )
    values = np.apply_along_axis(normalize, 1, values)
    weights = predictions.get("weight", pd.Series([1.0] * len(predictions))).to_numpy(dtype=float)
    weights = np.clip(weights, 0.0, None)
    if weights.sum() <= 0:
        weights = np.repeat(1.0, len(predictions))
    return normalize(np.average(values, axis=0, weights=weights))


def external_probability_dict(predictions: pd.DataFrame) -> dict[str, float]:
    return dict(zip(OUTCOMES, aggregate_external_predictions(predictions)))
