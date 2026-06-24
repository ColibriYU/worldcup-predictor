from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


TODAY_MATCHES = [
    {
        "match_id": "SUI-CAN-B",
        "matchday_date": "2026-06-24",
        "fixture_date_utc": "2026-06-24",
        "local_date_cn": "2026-06-25",
        "kickoff_utc": "2026-06-24T19:00:00Z",
        "kickoff_cn": "2026-06-25 03:00",
        "group": "Group B",
        "home_team": "Switzerland",
        "away_team": "Canada",
        "venue": "San Francisco Bay Area Stadium",
        "status": "Scheduled",
        "home_score": "",
        "away_score": "",
        "source": "FIFA",
        "source_url": "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026",
        "notes": "Official 2026-06-24 fixture prediction",
    },
    {
        "match_id": "BIH-QAT-C",
        "matchday_date": "2026-06-24",
        "fixture_date_utc": "2026-06-24",
        "local_date_cn": "2026-06-25",
        "kickoff_utc": "2026-06-24T22:00:00Z",
        "kickoff_cn": "2026-06-25 06:00",
        "group": "Group C",
        "home_team": "Bosnia and Herzegovina",
        "away_team": "Qatar",
        "venue": "Seattle Stadium",
        "status": "Scheduled",
        "home_score": "",
        "away_score": "",
        "source": "FIFA",
        "source_url": "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026",
        "notes": "Official 2026-06-24 fixture prediction",
    },
    {
        "match_id": "SCO-BRA-C",
        "matchday_date": "2026-06-24",
        "fixture_date_utc": "2026-06-24",
        "local_date_cn": "2026-06-25",
        "kickoff_utc": "2026-06-24T22:00:00Z",
        "kickoff_cn": "2026-06-25 06:00",
        "group": "Group C",
        "home_team": "Scotland",
        "away_team": "Brazil",
        "venue": "Miami Stadium",
        "status": "Scheduled",
        "home_score": "",
        "away_score": "",
        "source": "FIFA",
        "source_url": "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026",
        "notes": "Official 2026-06-24 fixture prediction",
    },
    {
        "match_id": "MAR-HAI-B",
        "matchday_date": "2026-06-24",
        "fixture_date_utc": "2026-06-24",
        "local_date_cn": "2026-06-25",
        "kickoff_utc": "2026-06-25T01:00:00Z",
        "kickoff_cn": "2026-06-25 09:00",
        "group": "Group B",
        "home_team": "Morocco",
        "away_team": "Haiti",
        "venue": "Atlanta Stadium",
        "status": "Scheduled",
        "home_score": "",
        "away_score": "",
        "source": "FIFA",
        "source_url": "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026",
        "notes": "Official 2026-06-24 fixture prediction",
    },
    {
        "match_id": "CZE-MEX-A",
        "matchday_date": "2026-06-24",
        "fixture_date_utc": "2026-06-25",
        "local_date_cn": "2026-06-25",
        "kickoff_utc": "2026-06-25T01:00:00Z",
        "kickoff_cn": "2026-06-25 09:00",
        "group": "Group A",
        "home_team": "Czechia",
        "away_team": "Mexico",
        "venue": "Mexico City Stadium",
        "status": "Scheduled",
        "home_score": "",
        "away_score": "",
        "source": "FIFA",
        "source_url": "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026",
        "notes": "Official 2026-06-24 fixture prediction",
    },
    {
        "match_id": "RSA-KOR-H",
        "matchday_date": "2026-06-24",
        "fixture_date_utc": "2026-06-25",
        "local_date_cn": "2026-06-25",
        "kickoff_utc": "2026-06-25T01:00:00Z",
        "kickoff_cn": "2026-06-25 09:00",
        "group": "Group H",
        "home_team": "South Africa",
        "away_team": "Korea Republic",
        "venue": "Estadio Monterrey",
        "status": "Scheduled",
        "home_score": "",
        "away_score": "",
        "source": "FIFA",
        "source_url": "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026",
        "notes": "Official 2026-06-24 fixture prediction",
    },
]

TEAM_STATS = [
    ("Switzerland", 1768, 1.54, 0.98),
    ("Canada", 1672, 1.28, 1.08),
    ("Bosnia and Herzegovina", 1628, 1.18, 1.14),
    ("Qatar", 1554, 1.02, 1.22),
    ("Scotland", 1662, 1.25, 1.09),
    ("Morocco", 1785, 1.58, 0.92),
    ("Haiti", 1428, 0.82, 1.34),
    ("Czechia", 1704, 1.40, 1.04),
    ("Mexico", 1748, 1.52, 0.99),
    ("South Africa", 1588, 1.06, 1.16),
    ("Korea Republic", 1735, 1.46, 1.00),
]

GROUP_STANDINGS = [
    ("Group A", "Mexico", 2, 2, 0, 0, 6, 4, 1, 3, "已出线，争小组头名", "6分球队可能根据对手和淘汰赛路径选择轮换或控节奏"),
    ("Group A", "Czechia", 2, 1, 0, 1, 3, 2, 2, 0, "争取出线", "本场至少需要拿分，落后时会提高冒险程度"),
    ("Group A", "South Africa", 2, 0, 1, 1, 1, 1, 3, -2, "必须抢分", "需要胜利才有更清晰的出线路径"),
    ("Group A", "Korea Republic", 2, 0, 1, 1, 1, 2, 3, -1, "必须抢分", "平局可能不够，后段可能主动提速"),
    ("Group B", "Morocco", 2, 2, 0, 0, 6, 5, 1, 4, "已出线，可能轮换", "6分在手，存在保存主力和控制伤病风险的动机"),
    ("Group B", "Switzerland", 2, 1, 0, 1, 3, 3, 2, 1, "争取出线", "赢球可基本锁定主动权，平局仍需看其他结果"),
    ("Group B", "Canada", 2, 1, 0, 1, 3, 2, 3, -1, "争取出线", "仍有出线主动权，本场不会轻易放弃对攻机会"),
    ("Group B", "Haiti", 2, 0, 0, 2, 0, 1, 5, -4, "必须抢分", "只有赢球才可能保留希望，比赛后段可能更开放"),
    ("Group C", "Brazil", 2, 2, 0, 0, 6, 5, 1, 4, "已出线，可能轮换", "6分在手，强队有轮换和控制比赛强度的空间"),
    ("Group C", "Scotland", 2, 1, 0, 1, 3, 2, 3, -1, "争取出线", "拿分价值很高，低位防守和定位球会是主要路径"),
    ("Group C", "Bosnia and Herzegovina", 2, 0, 1, 1, 1, 2, 3, -1, "必须抢分", "若迟迟打不开局面，后段会更早冒险"),
    ("Group C", "Qatar", 2, 0, 1, 1, 1, 1, 3, -2, "必须抢分", "仍需抢分，可能通过控球和低节奏争取机会"),
    ("Group H", "Korea Republic", 2, 1, 0, 1, 3, 3, 2, 1, "争取出线", "赢球可显著提高晋级概率，战意较高"),
    ("Group H", "South Africa", 2, 0, 1, 1, 1, 1, 3, -2, "必须抢分", "需要抢分，落后时会提高压上风险"),
]

XG_INPUTS = [
    ("SUI-CAN-B", "Switzerland", 1.02, 1.00, 0.98, 0.99, 0.22, 1.00),
    ("SUI-CAN-B", "Canada", 0.95, 0.96, 1.05, 1.09, 0.18, 1.01),
    ("BIH-QAT-C", "Bosnia and Herzegovina", 0.96, 0.97, 1.03, 0.98, 0.20, 0.99),
    ("BIH-QAT-C", "Qatar", 0.88, 0.90, 1.12, 1.04, 0.17, 0.98),
    ("SCO-BRA-C", "Scotland", 0.92, 0.93, 1.09, 1.02, 0.21, 0.98),
    ("SCO-BRA-C", "Brazil", 1.12, 1.08, 0.92, 1.09, 0.23, 1.03),
    ("MAR-HAI-B", "Morocco", 1.05, 1.04, 0.95, 1.03, 0.24, 1.01),
    ("MAR-HAI-B", "Haiti", 0.78, 0.84, 1.22, 1.06, 0.14, 0.96),
    ("CZE-MEX-A", "Czechia", 0.98, 0.99, 1.02, 0.98, 0.22, 1.00),
    ("CZE-MEX-A", "Mexico", 1.02, 1.02, 0.99, 1.03, 0.21, 1.01),
    ("RSA-KOR-H", "South Africa", 0.90, 0.92, 1.10, 1.05, 0.17, 0.98),
    ("RSA-KOR-H", "Korea Republic", 1.00, 1.01, 0.99, 1.04, 0.20, 1.00),
]

TEAM_FORM = [
    ("Switzerland", 5, 1.50, 0.99, 7.3, 5.2, 5, 1.00),
    ("Canada", 5, 1.25, 1.08, 6.4, 6.1, 5, 1.00),
    ("Bosnia and Herzegovina", 5, 1.16, 1.13, 5.7, 6.5, 5, 0.98),
    ("Qatar", 5, 1.03, 1.20, 5.0, 6.9, 5, 0.97),
    ("Scotland", 5, 1.22, 1.09, 6.0, 6.1, 5, 0.99),
    ("Morocco", 5, 1.55, 0.94, 7.9, 4.9, 5, 1.02),
    ("Haiti", 5, 0.84, 1.32, 4.0, 7.4, 5, 0.96),
    ("Czechia", 5, 1.38, 1.05, 6.8, 5.7, 5, 1.00),
    ("Mexico", 5, 1.50, 1.00, 7.4, 5.4, 5, 1.01),
    ("South Africa", 5, 1.06, 1.15, 5.3, 6.4, 5, 0.98),
    ("Korea Republic", 5, 1.43, 1.02, 7.0, 5.5, 5, 1.01),
]

EXTERNAL_PREDICTIONS = {
    "SUI-CAN-B": [(0.47, 0.27, 0.26), (0.45, 0.28, 0.27), (0.48, 0.26, 0.26)],
    "BIH-QAT-C": [(0.45, 0.28, 0.27), (0.43, 0.29, 0.28), (0.46, 0.27, 0.27)],
    "SCO-BRA-C": [(0.16, 0.22, 0.62), (0.17, 0.24, 0.59), (0.15, 0.23, 0.62)],
    "MAR-HAI-B": [(0.66, 0.22, 0.12), (0.64, 0.23, 0.13), (0.67, 0.21, 0.12)],
    "CZE-MEX-A": [(0.32, 0.28, 0.40), (0.34, 0.27, 0.39), (0.31, 0.29, 0.40)],
    "RSA-KOR-H": [(0.25, 0.28, 0.47), (0.26, 0.29, 0.45), (0.24, 0.28, 0.48)],
}

MATCHUP_FACTORS = [
    ("SUI-CAN-B", 1.01, 1.00, "瑞士整体纪律更稳，加拿大速度型转换会制造纵深压力"),
    ("BIH-QAT-C", 1.02, 0.99, "波黑身高和定位球优势明显，卡塔尔需要通过控球降低对抗强度"),
    ("SCO-BRA-C", 0.97, 1.06, "巴西一对一和肋部推进优势明显，苏格兰需要依靠身体对抗和定位球"),
    ("MAR-HAI-B", 1.06, 0.95, "摩洛哥边路和中场压迫更强，海地主要依赖反击速度"),
    ("CZE-MEX-A", 1.00, 1.03, "墨西哥主场氛围和前场灵活性略占优，捷克定位球可抵消部分差距"),
    ("RSA-KOR-H", 0.98, 1.04, "韩国转换速度和前场跑动更有威胁，南非需要提高防线横移质量"),
]

FACTORS = [
    ("SUI-CAN-B", "Switzerland", "positive", "瑞士阵型纪律稳定，适合控制中低节奏比赛"),
    ("SUI-CAN-B", "Canada", "positive", "加拿大边路速度和转换冲击能放大反击威胁"),
    ("BIH-QAT-C", "Bosnia and Herzegovina", "positive", "波黑定位球和高点优势是主要破局路径"),
    ("BIH-QAT-C", "Qatar", "positive", "卡塔尔若能降低比赛节奏，有机会把比赛拖入均势"),
    ("SCO-BRA-C", "Brazil", "positive", "巴西前场个人能力和转换质量明显更高"),
    ("SCO-BRA-C", "Scotland", "positive", "苏格兰身体对抗和定位球能提高冷门路径"),
    ("MAR-HAI-B", "Morocco", "positive", "摩洛哥攻守平衡更好，边路压迫有利于制造连续机会"),
    ("MAR-HAI-B", "Haiti", "positive", "海地反击速度是主要威胁，低比分能提高爆冷可能"),
    ("CZE-MEX-A", "Mexico", "positive", "墨西哥主场氛围和前场压迫会增强开局强度"),
    ("CZE-MEX-A", "Czechia", "positive", "捷克身体对抗和定位球质量有机会制造高价值机会"),
    ("RSA-KOR-H", "Korea Republic", "positive", "韩国前场跑动和快速转移更适合拉开空间"),
    ("RSA-KOR-H", "South Africa", "positive", "南非若稳住低位防守，反击和定位球会提高不败概率"),
]

ODDS = {
    "SUI-CAN-B": [(2.05, 3.35, 3.70, 2.00, 3.42, 3.85, 2.5), (2.08, 3.30, 3.65, 2.03, 3.40, 3.78, 2.5), (2.02, 3.38, 3.75, 1.98, 3.45, 3.90, 2.25)],
    "BIH-QAT-C": [(2.12, 3.25, 3.60, 2.05, 3.35, 3.85, 2.25), (2.16, 3.20, 3.55, 2.10, 3.30, 3.75, 2.25), (2.10, 3.28, 3.65, 2.06, 3.32, 3.82, 2.5)],
    "SCO-BRA-C": [(6.50, 4.20, 1.55, 7.20, 4.45, 1.48, 2.75), (6.30, 4.10, 1.57, 6.90, 4.35, 1.50, 2.75), (6.70, 4.25, 1.53, 7.40, 4.50, 1.47, 3.0)],
    "MAR-HAI-B": [(1.45, 4.45, 7.80, 1.39, 4.80, 8.80, 2.5), (1.47, 4.35, 7.50, 1.41, 4.70, 8.40, 2.5), (1.44, 4.50, 7.90, 1.38, 4.85, 8.90, 2.75)],
    "CZE-MEX-A": [(3.05, 3.25, 2.35, 3.15, 3.30, 2.28, 2.5), (3.00, 3.22, 2.40, 3.10, 3.28, 2.30, 2.5), (3.08, 3.20, 2.34, 3.18, 3.26, 2.26, 2.25)],
    "RSA-KOR-H": [(4.10, 3.45, 1.95, 4.30, 3.55, 1.88, 2.25), (4.00, 3.40, 1.98, 4.20, 3.50, 1.90, 2.25), (4.15, 3.48, 1.94, 4.35, 3.55, 1.87, 2.5)],
}

ALIASES = [
    ("Switzerland", "Switzerland"),
    ("Canada", "Canada"),
    ("Bosnia and Herzegovina", "Bosnia and Herzegovina"),
    ("Bosnia and Herzegovina", "Bosnia-Herzegovina"),
    ("Bosnia and Herzegovina", "Bosnia"),
    ("Qatar", "Qatar"),
    ("Scotland", "Scotland"),
    ("Morocco", "Morocco"),
    ("Haiti", "Haiti"),
    ("Czechia", "Czechia"),
    ("Czechia", "Czech Republic"),
    ("Mexico", "Mexico"),
    ("South Africa", "South Africa"),
    ("Korea Republic", "Korea Republic"),
    ("Korea Republic", "South Korea"),
    ("Korea Republic", "Republic of Korea"),
]


def upsert_rows(path: Path, rows: list[dict[str, object]], keys: list[str]) -> None:
    existing = pd.read_csv(path) if path.exists() else pd.DataFrame()
    incoming = pd.DataFrame(rows)
    combined = pd.concat([existing, incoming], ignore_index=True)
    combined = combined.drop_duplicates(subset=keys, keep="last")
    combined.to_csv(path, index=False, encoding="utf-8")


def main() -> None:
    matches_rows = [
        {
            "match_id": item["match_id"],
            "group": item["group"],
            "home_team": item["home_team"],
            "away_team": item["away_team"],
            "neutral_site": "true",
            "notes": item["notes"],
        }
        for item in TODAY_MATCHES
    ]
    schedule_rows = [
        {key: value for key, value in item.items() if key != "notes"} for item in TODAY_MATCHES
    ]
    team_rows = [
        {
            "team": team,
            "elo": elo,
            "attack_strength": attack,
            "defense_factor": defense,
        }
        for team, elo, attack, defense in TEAM_STATS
    ]
    xg_rows = [
        {
            "match_id": match_id,
            "team": team,
            "shot_quality": shot_quality,
            "shot_location": shot_location,
            "defensive_pressure": defensive_pressure,
            "transition_attack": transition_attack,
            "set_piece_xg": set_piece_xg,
            "tempo_factor": tempo_factor,
        }
        for match_id, team, shot_quality, shot_location, defensive_pressure, transition_attack, set_piece_xg, tempo_factor in XG_INPUTS
    ]
    form_rows = [
        {
            "team": team,
            "matches_played": matches_played,
            "prior_attack": prior_attack,
            "prior_defense": prior_defense,
            "recent_xg_for": recent_xg_for,
            "recent_xg_against": recent_xg_against,
            "recent_matches": recent_matches,
            "form_multiplier": form_multiplier,
        }
        for team, matches_played, prior_attack, prior_defense, recent_xg_for, recent_xg_against, recent_matches, form_multiplier in TEAM_FORM
    ]
    external_rows = []
    for match_id, probs in EXTERNAL_PREDICTIONS.items():
        for source, weight, (home, draw, away) in zip(
            ["Model Alpha", "Model Beta", "Analyst Consensus"],
            [1.00, 0.85, 0.90],
            probs,
        ):
            external_rows.append(
                {
                    "match_id": match_id,
                    "source": source,
                    "home_probability": home,
                    "draw_probability": draw,
                    "away_probability": away,
                    "weight": weight,
                }
            )
    matchup_rows = [
        {
            "match_id": match_id,
            "home_matchup_factor": home,
            "away_matchup_factor": away,
            "summary": summary,
        }
        for match_id, home, away, summary in MATCHUP_FACTORS
    ]
    factor_rows = [
        {
            "match_id": match_id,
            "team": team,
            "impact": impact,
            "description": description,
        }
        for match_id, team, impact, description in FACTORS
    ]
    odds_rows = []
    for match_id, rows in ODDS.items():
        for idx, row in enumerate(rows, start=1):
            open_home, open_draw, open_away, home, draw, away, total = row
            odds_rows.append(
                {
                    "match_id": match_id,
                    "bookmaker": f"Book {chr(64 + idx)}",
                    "open_home": open_home,
                    "open_draw": open_draw,
                    "open_away": open_away,
                    "home_odds": home,
                    "draw_odds": draw,
                    "away_odds": away,
                    "over_under_line": total,
                }
            )
    alias_rows = [{"internal_team": team, "alias": alias} for team, alias in ALIASES]
    standings_rows = [
        {
            "group": group,
            "team": team,
            "played": played,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "points": points,
            "goals_for": goals_for,
            "goals_against": goals_against,
            "goal_difference": goal_difference,
            "status": status,
            "note": note,
        }
        for group, team, played, wins, draws, losses, points, goals_for, goals_against, goal_difference, status, note in GROUP_STANDINGS
    ]

    upsert_rows(DATA / "matches.csv", matches_rows, ["match_id"])
    upsert_rows(DATA / "worldcup_schedule.csv", schedule_rows, ["match_id"])
    upsert_rows(DATA / "team_stats.csv", team_rows, ["team"])
    upsert_rows(DATA / "xg_inputs.csv", xg_rows, ["match_id", "team"])
    upsert_rows(DATA / "team_form.csv", form_rows, ["team"])
    upsert_rows(DATA / "external_predictions.csv", external_rows, ["match_id", "source"])
    upsert_rows(DATA / "matchup_factors.csv", matchup_rows, ["match_id"])
    upsert_rows(DATA / "factors.csv", factor_rows, ["match_id", "team", "description"])
    upsert_rows(DATA / "odds.csv", odds_rows, ["match_id", "bookmaker"])
    upsert_rows(DATA / "team_aliases.csv", alias_rows, ["internal_team", "alias"])
    upsert_rows(DATA / "group_standings.csv", standings_rows, ["group", "team"])


if __name__ == "__main__":
    main()
