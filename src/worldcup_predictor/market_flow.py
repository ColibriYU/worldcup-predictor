from __future__ import annotations

import numpy as np
import pandas as pd

from .probability import OUTCOMES, market_bias, normalize


def market_flow_probabilities(match_odds: pd.DataFrame, *, sensitivity: float = 5.0) -> np.ndarray:
    bias = market_bias(match_odds)
    centered = bias - bias.mean()
    scores = np.exp(np.clip(centered * sensitivity, -2.0, 2.0))
    return normalize(scores)


def market_flow_flags(match_odds: pd.DataFrame, *, is_live: bool = True) -> list[str]:
    bias = dict(zip(OUTCOMES, market_bias(match_odds)))
    flags: list[str] = []
    max_abs_bias = max(abs(value) for value in bias.values())

    if not is_live:
        flags.append("当前使用本地样例盘口，盘口流只是演示信号；接入 Odds API 并形成多次历史快照后，资金方向判断才更可靠。")

    if max_abs_bias < 0.008:
        flags.append("初盘到当前盘变化很小，暂未形成可读的盘口流信号。")
        return flags

    signal_label = "明显" if max_abs_bias >= 0.03 else "轻微"
    if bias["home"] > 0.012 and bias["away"] < 0:
        flags.append(f"主胜隐含概率{signal_label}上升，市场更偏向主队方向。")
    if bias["away"] > 0.012 and bias["home"] < 0:
        flags.append(f"客胜隐含概率{signal_label}上升，市场更偏向客队方向。")
    if bias["draw"] > 0.012:
        flags.append(f"平局隐含概率{signal_label}上升，低比分/僵持区间值得关注。")
    elif bias["draw"] < -0.012:
        flags.append(f"平局隐含概率{signal_label}下降，市场更倾向比赛分出胜负。")

    if len(flags) == (0 if is_live else 1):
        flags.append("盘口流变化温和，当前市场没有明显单边资金信号。")
    return flags
