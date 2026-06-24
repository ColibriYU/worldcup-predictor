from __future__ import annotations

import pandas as pd


def _team_row(standings: pd.DataFrame, team: str) -> pd.Series | None:
    if standings.empty:
        return None
    rows = standings[standings["team"].str.casefold() == team.casefold()]
    if rows.empty:
        return None
    return rows.iloc[0]


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


def group_stage_factors(fixtures: pd.DataFrame, standings: pd.DataFrame) -> pd.DataFrame:
    if fixtures.empty or standings.empty:
        return pd.DataFrame(columns=["match_id", "team", "impact", "description"])

    rows: list[dict[str, object]] = []
    for _, match in fixtures.iterrows():
        for team in [str(match["home_team"]), str(match["away_team"])]:
            row = _team_row(standings, team)
            if row is None:
                continue
            impact, description = _motivation(row)
            rows.append(
                {
                    "match_id": match["match_id"],
                    "team": team,
                    "impact": impact,
                    "description": description,
                }
            )
    return pd.DataFrame(rows)
