from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd


Finish = Literal["winner", "runner_up", "third", "outside"]
Outcome = Literal["win", "draw", "loss"]

OUTCOME_LABELS: dict[Outcome, str] = {
    "win": "胜",
    "draw": "平",
    "loss": "负",
}

FINISH_LABELS: dict[Finish, str] = {
    "winner": "小组第1",
    "runner_up": "小组第2",
    "third": "小组第3",
    "outside": "小组第4",
}


@dataclass(frozen=True)
class SimulatedStanding:
    team: str
    group: str
    points: int
    goal_difference: int
    goals_for: int
    status: str = ""
    note: str = ""


@dataclass(frozen=True)
class TeamScenario:
    outcome: Outcome
    points: int
    finish: Finish
    qualification_score: float
    path_pressure: float
    opponent_hint: str
    path_note: str


def _team_row(standings: pd.DataFrame, team: str) -> pd.Series | None:
    if standings.empty:
        return None
    rows = standings[standings["team"].str.casefold() == team.casefold()]
    if rows.empty:
        return None
    return rows.iloc[0]


def _group_rows(standings: pd.DataFrame, group: str) -> pd.DataFrame:
    if standings.empty or "group" not in standings.columns:
        return pd.DataFrame()
    return standings[standings["group"].astype(str).str.casefold() == str(group).casefold()].copy()


def _path_row(paths: pd.DataFrame | None, group: str, finish: Finish) -> pd.Series | None:
    if paths is None or paths.empty or finish == "outside":
        return None
    rows = paths[
        (paths["group"].astype(str).str.casefold() == str(group).casefold())
        & (paths["finish"].astype(str).str.casefold() == finish.casefold())
    ]
    if rows.empty:
        return None
    return rows.iloc[0]


def _opponent_strength(
    *,
    path: pd.Series | None,
    team_stats: pd.DataFrame | None,
    standings: pd.DataFrame,
    team: str,
) -> tuple[float, str]:
    if path is None:
        return 0.5, "暂无明确淘汰赛对手路径"

    hint = str(path.get("opponent_slot", ""))
    groups_text = str(path.get("opponent_groups", ""))
    groups = [value.strip() for value in groups_text.split(";") if value.strip()]
    if team_stats is None or team_stats.empty or not groups:
        return 0.5, hint or "淘汰赛路径待定"

    candidates = standings[standings["group"].isin([f"Group {g}" if len(g) == 1 else g for g in groups])]
    if candidates.empty:
        candidates = standings[standings["group"].astype(str).str[-1].isin(groups)]
    candidates = candidates[candidates["team"].astype(str).str.casefold() != team.casefold()]
    if candidates.empty:
        return 0.5, hint or "淘汰赛路径待定"

    merged = candidates.merge(team_stats[["team", "elo"]], on="team", how="left")
    if merged["elo"].notna().any():
        avg_elo = float(merged["elo"].dropna().mean())
        max_elo = float(merged["elo"].dropna().max())
        pressure = np.clip((0.65 * avg_elo + 0.35 * max_elo - 1600) / 450, 0.0, 1.0)
        strongest = merged.sort_values("elo", ascending=False).iloc[0]
        hint = hint or f"可能遇到 {strongest['team']}"
        return float(pressure), hint

    return 0.5, hint or "淘汰赛路径待定"


def _standing_from_row(row: pd.Series) -> SimulatedStanding:
    return SimulatedStanding(
        team=str(row["team"]),
        group=str(row["group"]),
        points=int(row["points"]),
        goal_difference=int(row.get("goal_difference", 0)),
        goals_for=int(row.get("goals_for", 0)),
        status=str(row.get("status", "")),
        note=str(row.get("note", "")),
    )


def _simulate_row(row: pd.Series, *, points_delta: int, goal_delta: int, goals_for_delta: int) -> SimulatedStanding:
    base = _standing_from_row(row)
    return SimulatedStanding(
        team=base.team,
        group=base.group,
        points=base.points + points_delta,
        goal_difference=base.goal_difference + goal_delta,
        goals_for=base.goals_for + goals_for_delta,
        status=base.status,
        note=base.note,
    )


def _rank_group(rows: list[SimulatedStanding]) -> list[SimulatedStanding]:
    return sorted(
        rows,
        key=lambda item: (item.points, item.goal_difference, item.goals_for),
        reverse=True,
    )


def _finish_for_rank(rank: int) -> Finish:
    if rank == 1:
        return "winner"
    if rank == 2:
        return "runner_up"
    if rank == 3:
        return "third"
    return "outside"


def _qualification_score(finish: Finish, points: int, goal_difference: int) -> float:
    if finish == "winner":
        return 1.0
    if finish == "runner_up":
        return 0.92
    if finish == "third":
        if points >= 4:
            return 0.76
        if points == 3:
            return 0.42 + min(max(goal_difference, -3), 3) * 0.05
        return 0.12
    return 0.02 if points <= 1 else 0.08


def _third_round_signal(row: pd.Series) -> bool:
    played = int(row.get("played", 0))
    status = str(row.get("status", "")).casefold()
    return played >= 2 or any(token in status for token in ["争取出线", "必须抢分", "已出线", "qualified"])


def _team_scenarios(
    *,
    team: str,
    opponent: str,
    group: str,
    standings: pd.DataFrame,
    paths: pd.DataFrame | None,
    team_stats: pd.DataFrame | None,
) -> list[TeamScenario]:
    group_frame = _group_rows(standings, group)
    team_row = _team_row(group_frame, team)
    opponent_row = _team_row(group_frame, opponent)
    if team_row is None or opponent_row is None:
        return []

    scenarios: list[TeamScenario] = []
    outcome_params: dict[Outcome, tuple[int, int, int, int, int, int]] = {
        # team points, team GD, team GF, opponent points, opponent GD, opponent GF
        "win": (3, 1, 1, 0, -1, 0),
        "draw": (1, 0, 1, 1, 0, 1),
        "loss": (0, -1, 0, 3, 1, 1),
    }

    for outcome, params in outcome_params.items():
        team_points, team_gd, team_gf, opp_points, opp_gd, opp_gf = params
        simulated: list[SimulatedStanding] = []
        for _, row in group_frame.iterrows():
            row_team = str(row["team"])
            if row_team.casefold() == team.casefold():
                simulated.append(
                    _simulate_row(row, points_delta=team_points, goal_delta=team_gd, goals_for_delta=team_gf)
                )
            elif row_team.casefold() == opponent.casefold():
                simulated.append(
                    _simulate_row(row, points_delta=opp_points, goal_delta=opp_gd, goals_for_delta=opp_gf)
                )
            else:
                simulated.append(_standing_from_row(row))

        ranked = _rank_group(simulated)
        rank = next((idx + 1 for idx, item in enumerate(ranked) if item.team.casefold() == team.casefold()), 4)
        simulated_team = next(item for item in ranked if item.team.casefold() == team.casefold())
        finish = _finish_for_rank(rank)
        path = _path_row(paths, group, finish)
        path_pressure, hint = _opponent_strength(
            path=path,
            team_stats=team_stats,
            standings=standings,
            team=team,
        )
        scenarios.append(
            TeamScenario(
                outcome=outcome,
                points=simulated_team.points,
                finish=finish,
                qualification_score=_qualification_score(
                    finish,
                    simulated_team.points,
                    simulated_team.goal_difference,
                ),
                path_pressure=path_pressure,
                opponent_hint=hint,
                path_note=str(path.get("path_note", "")) if path is not None else "",
            )
        )

    return scenarios


def _scenario_value(scenario: TeamScenario) -> float:
    finish_bonus = {
        "winner": 0.28,
        "runner_up": 0.17,
        "third": -0.02,
        "outside": -0.45,
    }[scenario.finish]
    return scenario.qualification_score + finish_bonus - 0.16 * scenario.path_pressure


def _team_context(
    *,
    team: str,
    opponent: str,
    group: str,
    standings: pd.DataFrame,
    paths: pd.DataFrame | None,
    team_stats: pd.DataFrame | None,
) -> dict[str, object] | None:
    group_frame = _group_rows(standings, group)
    row = _team_row(group_frame, team)
    if row is None or not _third_round_signal(row):
        return None

    scenarios = _team_scenarios(
        team=team,
        opponent=opponent,
        group=group,
        standings=standings,
        paths=paths,
        team_stats=team_stats,
    )
    if not scenarios:
        return None

    by_outcome = {scenario.outcome: scenario for scenario in scenarios}
    values = {outcome: _scenario_value(scenario) for outcome, scenario in by_outcome.items()}
    win_need = values["win"] - max(values["draw"], values["loss"])
    draw_value = values["draw"] - values["loss"]
    path_gap = by_outcome["win"].path_pressure - by_outcome["draw"].path_pressure
    risk_of_exit = 1.0 - by_outcome["loss"].qualification_score
    status_text = f"{row.get('status', '')} {row.get('note', '')}"
    already_qualified = int(row["points"]) >= 6 or "已出线" in status_text or "qualified" in status_text.casefold()
    must_chase = any(token in status_text for token in ["必须抢分", "只有赢球", "需要胜利", "平局可能不够"])
    needs_result = any(token in status_text for token in ["争取出线", "至少需要拿分", "赢球可", "主动权"])

    if (
        already_qualified
        and by_outcome["win"].finish == "winner"
        and by_outcome["win"].path_pressure > by_outcome["draw"].path_pressure + 0.12
    ):
        posture = "manage_path"
        attack_delta = -0.04
        defense_delta = -0.04
        draw_delta = 0.04
        label = "可能管理排名路径"
    elif already_qualified:
        posture = "rotate"
        attack_delta = -0.06
        defense_delta = -0.03
        draw_delta = 0.03
        label = "已出线可能轮换"
    elif must_chase:
        posture = "must_win"
        attack_delta = 0.11
        defense_delta = 0.05
        draw_delta = -0.05
        label = "必须争胜"
    elif by_outcome["win"].qualification_score < 0.7:
        posture = "must_win"
        attack_delta = 0.11
        defense_delta = 0.05
        draw_delta = -0.05
        label = "必须争胜"
    elif win_need >= 0.24 or risk_of_exit >= 0.7:
        posture = "chase_win"
        attack_delta = 0.07
        defense_delta = 0.03
        draw_delta = -0.03
        label = "争胜动力强"
    elif draw_value >= 0.34 and by_outcome["draw"].qualification_score >= 0.72:
        posture = "protect_draw"
        attack_delta = -0.03
        defense_delta = -0.07
        draw_delta = 0.06
        label = "平局价值高"
    elif needs_result and by_outcome["draw"].qualification_score >= 0.72:
        posture = "protect_draw"
        attack_delta = -0.03
        defense_delta = -0.07
        draw_delta = 0.06
        label = "平局价值高"
    elif needs_result:
        posture = "chase_win"
        attack_delta = 0.07
        defense_delta = 0.03
        draw_delta = -0.03
        label = "争胜动力强"
    elif by_outcome["win"].finish == "winner" and by_outcome["win"].path_pressure > by_outcome["draw"].path_pressure + 0.12:
        posture = "manage_path"
        attack_delta = -0.04
        defense_delta = -0.04
        draw_delta = 0.04
        label = "可能管理排名路径"
    else:
        posture = "balanced"
        attack_delta = 0.02
        defense_delta = 0.0
        draw_delta = 0.0
        label = "战意正常"

    return {
        "team": team,
        "points": int(row["points"]),
        "status": str(row.get("status", "")),
        "note": str(row.get("note", "")),
        "posture": posture,
        "label": label,
        "attack_delta": attack_delta,
        "defense_delta": defense_delta,
        "draw_delta": draw_delta,
        "win_need": float(win_need),
        "draw_value": float(draw_value),
        "path_gap": float(path_gap),
        "risk_of_exit": float(risk_of_exit),
        "scenarios": {
            outcome: {
                "points": scenario.points,
                "finish": scenario.finish,
                "finish_label": FINISH_LABELS[scenario.finish],
                "qualification_score": scenario.qualification_score,
                "path_pressure": scenario.path_pressure,
                "opponent_hint": scenario.opponent_hint,
                "path_note": scenario.path_note,
            }
            for outcome, scenario in by_outcome.items()
        },
    }


def group_stage_factors(fixtures: pd.DataFrame, standings: pd.DataFrame) -> pd.DataFrame:
    if fixtures.empty or standings.empty:
        return pd.DataFrame(columns=["match_id", "team", "impact", "description"])

    rows: list[dict[str, object]] = []
    for _, match in fixtures.iterrows():
        group_frame = _group_rows(standings, str(match["group"]))
        for team in [str(match["home_team"]), str(match["away_team"])]:
            row = _team_row(group_frame, team)
            if row is None:
                continue
            context = _team_context(
                team=team,
                opponent=str(match["away_team"] if team == str(match["home_team"]) else match["home_team"]),
                group=str(match["group"]),
                standings=standings,
                paths=None,
                team_stats=None,
            )
            if context is None:
                impact, description = _motivation(row)
            else:
                impact = "positive" if context["posture"] in {"must_win", "chase_win"} else "negative"
                description = (
                    f"小组形势：目前 {context['points']} 分，{context['status']}。"
                    f"{context['label']}；{context['note']}"
                )
            rows.append(
                {
                    "match_id": match["match_id"],
                    "team": team,
                    "impact": impact,
                    "description": description,
                }
            )
    return pd.DataFrame(rows)


def _motivation(row: pd.Series) -> tuple[str, str]:
    points = int(row["points"])
    status = str(row.get("status", ""))
    note = str(row.get("note", ""))

    if "锁定头名" in status or "group winner" in status.casefold():
        return (
            "negative",
            f"小组形势：目前 {points} 分，{status}。已基本完成小组目标，存在轮换、控节奏和降低伤病风险的可能；{note}",
        )
    if "已出线" in status or "qualified" in status.casefold():
        return (
            "negative",
            f"小组形势：目前 {points} 分，{status}。出线压力较小，若赛程密集，主帅可能保留部分主力；{note}",
        )
    if points >= 4:
        return (
            "positive",
            f"小组形势：目前 {points} 分，前二/第三名出线主动权较强。本场既有争小组排名动力，也可能优先避免大比分失控；{note}",
        )
    if points == 3:
        return (
            "positive",
            f"小组形势：目前 {points} 分，赢球可显著提高出线确定性，平局则可能要看其他小组和净胜球；{note}",
        )
    if "出局" in status or "eliminated" in status.casefold():
        return (
            "negative",
            f"小组形势：目前 {points} 分，{status}。战意和轮换存在不确定性，但也可能踢得更开放；{note}",
        )
    return (
        "positive",
        f"小组形势：目前 {points} 分，必须抢分才有更清晰的出线路径。落后时更可能提前冒险压上；{note}",
    )


def knockout_context(
    match: pd.Series,
    standings: pd.DataFrame | None,
    paths: pd.DataFrame | None = None,
    team_stats: pd.DataFrame | None = None,
) -> dict[str, object]:
    if standings is None or standings.empty:
        return {
            "available": False,
            "probability_delta": np.zeros(3),
            "lambda_multiplier": {"home": 1.0, "away": 1.0},
            "draw_multiplier": 1.0,
            "home": None,
            "away": None,
            "summary": "暂无小组出线路径数据",
        }

    home_team = str(match["home_team"])
    away_team = str(match["away_team"])
    group = str(match["group"])
    home_context = _team_context(
        team=home_team,
        opponent=away_team,
        group=group,
        standings=standings,
        paths=paths,
        team_stats=team_stats,
    )
    away_context = _team_context(
        team=away_team,
        opponent=home_team,
        group=group,
        standings=standings,
        paths=paths,
        team_stats=team_stats,
    )

    if home_context is None and away_context is None:
        return {
            "available": False,
            "probability_delta": np.zeros(3),
            "lambda_multiplier": {"home": 1.0, "away": 1.0},
            "draw_multiplier": 1.0,
            "home": home_context,
            "away": away_context,
            "summary": "非小组第三轮或缺少积分形势数据",
        }

    home_attack = float(home_context["attack_delta"]) if home_context else 0.0
    away_attack = float(away_context["attack_delta"]) if away_context else 0.0
    home_defense = float(home_context["defense_delta"]) if home_context else 0.0
    away_defense = float(away_context["defense_delta"]) if away_context else 0.0
    home_draw = float(home_context["draw_delta"]) if home_context else 0.0
    away_draw = float(away_context["draw_delta"]) if away_context else 0.0

    probability_delta = np.array(
        [
            home_attack - away_defense,
            (home_draw + away_draw) / 2,
            away_attack - home_defense,
        ],
        dtype=float,
    )
    probability_delta = np.clip(probability_delta, -0.12, 0.12)

    home_lambda_multiplier = float(np.clip(1 + home_attack + away_defense * 0.45, 0.86, 1.16))
    away_lambda_multiplier = float(np.clip(1 + away_attack + home_defense * 0.45, 0.86, 1.16))
    draw_multiplier = float(np.clip(1 + (home_draw + away_draw) / 2, 0.9, 1.1))

    labels = []
    if home_context:
        labels.append(f"{home_team}: {home_context['label']}")
    if away_context:
        labels.append(f"{away_team}: {away_context['label']}")

    return {
        "available": True,
        "probability_delta": probability_delta,
        "lambda_multiplier": {
            "home": home_lambda_multiplier,
            "away": away_lambda_multiplier,
        },
        "draw_multiplier": draw_multiplier,
        "home": home_context,
        "away": away_context,
        "summary": "；".join(labels),
    }
