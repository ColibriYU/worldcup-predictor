from __future__ import annotations

from datetime import datetime
from html import escape
import os
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from worldcup_predictor import PredictionConfig, predict_match
from worldcup_predictor.data import load_data
from worldcup_predictor.monitoring import bookmaker_value_bets, combined_value_bets, odds_change_summary
from worldcup_predictor.narrative import build_narrative_report


DATA_CACHE_VERSION = "group-context-v1"


def secret_value(name: str) -> str | None:
    try:
        value = st.secrets.get(name)
    except Exception:
        value = None
    return str(value).strip() if value else os.getenv(name)


def odds_update_slot(now: datetime | None = None) -> str:
    now = now or datetime.now(ZoneInfo("Asia/Shanghai"))
    if now.hour < 14:
        slot = "pre_1400"
    elif now.hour < 19:
        slot = "post_1400"
    else:
        slot = "post_1900"
    return f"{now.date().isoformat()}-{slot}"


def inject_style() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(180deg, #f4f8fb 0%, #eef5f2 42%, #f8fafc 100%);
        }
        div[data-testid="stHeader"] {
            background: rgba(244, 248, 251, 0.78);
        }
        .main .block-container {
            padding-top: 1.15rem;
            padding-bottom: 1.8rem;
            max-width: 1440px;
        }
        div[data-testid="stVerticalBlock"] {
            gap: 0.45rem;
        }
        div[data-testid="stHorizontalBlock"] {
            gap: 0.65rem;
        }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #dbe7e2;
            border-radius: 8px;
            padding: 8px 10px;
            box-shadow: 0 5px 14px rgba(15, 23, 42, 0.05);
        }
        div[data-testid="stMetricLabel"] {
            font-size: 0.78rem;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.35rem;
        }
        div[data-testid="stMetricValue"] {
            color: #0f766e;
        }
        div[data-testid="stMarkdownContainer"] p,
        div[data-testid="stMarkdownContainer"] li {
            margin-bottom: 0.22rem;
            line-height: 1.35;
        }
        div[data-testid="stExpander"] {
            border: 1px solid #dbe7e2;
            border-radius: 8px;
            background: #ffffff;
        }
        .status-band {
            padding: 10px 12px;
            border-radius: 8px;
            border: 1px solid #cfe3da;
            background: #ffffff;
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
            margin: 4px 0 12px;
        }
        .status-band strong {
            color: #0f766e;
        }
        .match-chip {
            display: inline-block;
            padding: 3px 9px;
            border-radius: 999px;
            color: #075985;
            background: #e0f2fe;
            border: 1px solid #bae6fd;
            font-size: 0.82rem;
            margin-bottom: 2px;
        }
        .score-line {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
            min-height: 24px;
            padding: 2px 8px;
            border-radius: 7px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            margin-bottom: 0;
            font-size: 0.88rem;
            font-variant-numeric: tabular-nums;
        }
        .score-list {
            display: grid;
            gap: 3px;
            margin: 0 0 4px;
        }
        .score-line span,
        .score-line b {
            line-height: 1.05;
        }
        .score-line b {
            color: #0f766e;
        }
        .index-box {
            background: #ffffff;
            border: 1px solid #dbe7e2;
            border-radius: 8px;
            padding: 7px 9px;
            margin: 4px 0;
        }
        .index-title {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 4px;
        }
        .index-pill-low,
        .index-pill-mid,
        .index-pill-high {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 0.78rem;
        }
        .index-pill-low {
            color: #166534;
            background: #dcfce7;
        }
        .index-pill-mid {
            color: #92400e;
            background: #fef3c7;
        }
        .index-pill-high {
            color: #991b1b;
            background: #fee2e2;
        }
        .index-bar {
            height: 8px;
            border-radius: 999px;
            background: #e2e8f0;
            overflow: hidden;
            margin-bottom: 5px;
        }
        .index-reason {
            color: #475569;
            font-size: 0.78rem;
            line-height: 1.22;
            margin-top: 1px;
        }
        .index-fill-upset {
            height: 100%;
            background: linear-gradient(90deg, #f59e0b, #ef4444);
        }
        .index-fill-goals {
            height: 100%;
            background: linear-gradient(90deg, #14b8a6, #2563eb);
        }
        .bet-box {
            background: #ffffff;
            border: 1px solid #dbe7e2;
            border-radius: 8px;
            padding: 7px 9px;
            margin: 4px 0;
        }
        .bet-title {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 8px;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 4px;
        }
        .bet-pill-good,
        .bet-pill-watch,
        .bet-pill-none {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 0.78rem;
            white-space: nowrap;
        }
        .bet-pill-good {
            color: #166534;
            background: #dcfce7;
        }
        .bet-pill-watch {
            color: #92400e;
            background: #fef3c7;
        }
        .bet-pill-none {
            color: #475569;
            background: #e2e8f0;
        }
        .bet-line {
            display: flex;
            justify-content: space-between;
            gap: 8px;
            color: #334155;
            font-size: 0.84rem;
            line-height: 1.28;
            font-variant-numeric: tabular-nums;
        }
        .bet-line b {
            color: #0f766e;
        }
        .bet-note {
            color: #64748b;
            font-size: 0.78rem;
            line-height: 1.28;
            margin-top: 4px;
        }
        .narrative-note {
            padding: 10px 12px;
            border-radius: 8px;
            background: #fff7ed;
            border: 1px solid #fed7aa;
            color: #7c2d12;
            margin: 8px 0 12px;
            font-size: 0.92rem;
        }
        .tarot-card {
            padding: 12px 14px;
            border-radius: 8px;
            border: 1px solid #ddd6fe;
            background: #fbfaff;
            margin: 10px 0;
        }
        .tarot-card strong {
            color: #5b21b6;
        }
        .narrative-summary {
            padding: 14px 16px;
            border-radius: 8px;
            border: 1px solid #c4b5fd;
            background: #f5f3ff;
            color: #312e81;
            line-height: 1.75;
            margin: 10px 0 14px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def render_score_list(frame: pd.DataFrame) -> None:
    lines = []
    for _, row in frame.iterrows():
        lines.append(
            "<div class='score-line'>"
            f"<span>{escape(str(row['score']))}</span>"
            f"<b>{float(row['probability_pct']):.1f}%</b>"
            "</div>"
        )
    st.markdown(f"<div class='score-list'>{''.join(lines)}</div>", unsafe_allow_html=True)


def pill_class(level: str) -> str:
    if level == "高":
        return "index-pill-high"
    if level == "中":
        return "index-pill-mid"
    return "index-pill-low"


def render_index_box(title: str, payload: dict[str, object], fill_class: str) -> None:
    index = float(payload["index"])
    level = str(payload["level"])
    reasons = "".join(
        f"<div class='index-reason'>- {escape(str(reason))}</div>"
        for reason in list(payload.get("reasons", []))[:3]
    )
    st.markdown(
        f"""
        <div class="index-box">
            <div class="index-title">
                <span>{escape(title)}</span>
                <span class="{pill_class(level)}">{escape(level)} · {index:.0f}</span>
            </div>
            <div class="index-bar"><div class="{fill_class}" style="width: {index:.0f}%"></div></div>
            {reasons}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_bet_box(match_odds: pd.DataFrame, prediction: dict[str, object], min_edge: float) -> None:
    value_bets = bookmaker_value_bets(
        match_odds,
        prediction["final_probability"],
        min_edge=min_edge,
    )
    if value_bets.empty:
        st.markdown(
            """
            <div class="bet-box">
                <div class="bet-title">
                    <span>值得下注</span>
                    <span class="bet-pill-none">暂无</span>
                </div>
                <div class="bet-note">当前胜平负方向没有达到设定 Edge 阈值，建议观望或等待赔率变化。</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    best = value_bets.iloc[0]
    edge = float(best["edge"])
    probability_gap = float(best["probability_gap"])
    level = "强关注" if edge >= max(0.08, min_edge * 2) and probability_gap > 0 else "可关注"
    pill_class_name = "bet-pill-good" if level == "强关注" else "bet-pill-watch"
    st.markdown(
        f"""
        <div class="bet-box">
            <div class="bet-title">
                <span>值得下注</span>
                <span class="{pill_class_name}">{escape(level)} · Edge {edge * 100:.1f}%</span>
            </div>
            <div class="bet-line"><span>方向</span><b>{escape(str(best['outcome_label']))}</b></div>
            <div class="bet-line"><span>公司 / 赔率</span><b>{escape(str(best['bookmaker']))} · {float(best['odds']):.2f}</b></div>
            <div class="bet-line"><span>模型概率 / 公允赔率</span><b>{pct(float(best['model_probability']))} · {float(best['fair_odds']):.2f}</b></div>
            <div class="bet-note">只表示模型相对盘口有价格优势，不代表确定收益。</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_narrative_report(report: dict[str, object]) -> None:
    st.markdown(
        "<div class='narrative-note'>易经和塔罗只用于生成赛前叙事报告，不参与真实预测模型概率计算。</div>",
        unsafe_allow_html=True,
    )
    score_cols = st.columns(3)
    score_cols[0].metric("Narrative Score", f"{float(report['narrative_score']):+.2f}")
    score_cols[1].metric("易经贡献", f"{float(report['iching_contribution']):+.2f}")
    score_cols[2].metric("塔罗贡献", f"{float(report['tarot_contribution']):+.2f}")

    st.markdown("**整场比赛发展总结**")
    st.markdown(
        f"<div class='narrative-summary'>{report['summary']}</div>",
        unsafe_allow_html=True,
    )
    narrative_scores = list(report.get("narrative_scores", []))
    if narrative_scores:
        st.markdown("**叙事比分候选（1-2个，不改变量化概率）**")
        for item in narrative_scores:
            st.write(f"- {item['score']}：{item['tag']}。{item['reason']}")

    iching = report["iching"]
    st.markdown("**易经依据**")
    iching_cols = st.columns(3)
    iching_cols[0].metric("本卦", str(iching["hexagram"]))
    iching_cols[1].metric("动爻", f"第{int(iching['changing_line'])}爻")
    iching_cols[2].metric("变卦", str(iching["transformed"]))
    st.write(
        f"- 体用/月令：体卦 {iching['body_trigram']}{iching['body_element']} "
        f"处「{iching['body_state']}」；用卦 {iching['use_trigram']}{iching['use_element']} "
        f"处「{iching['use_state']}」；变卦用卦 {iching['transformed_use_trigram']}{iching['transformed_use_element']} "
        f"处「{iching['transformed_use_state']}」。"
    )
    st.write(f"- 本卦解释：{iching['primary_explanation']}")
    st.write(f"- 变卦解释：{iching['transformed_explanation']}")
    st.write(f"- 动爻解释：{iching['line_text']}")
    st.caption(str(iching["analysis"]))

    st.markdown("**塔罗依据**")
    st.write(f"- 三阶段线：{report['tarot']['timeline']}")
    st.write(f"- 综合牌意：{report['tarot']['synthesis']}")
    for card in report["tarot"]["cards"]:
        st.markdown(
            f"""
            <div class="tarot-card">
                <strong>{card['position']}：{card['name']}（{card['orientation']}）</strong><br>
                关键词：{'、'.join(card['keywords'])}<br>
                牌义：{card['meaning']}<br>
                正逆位解释：{card['orientation_meaning']}<br>
                比赛解读：{card['lean']}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_group_context(prediction: dict[str, object]) -> None:
    context = prediction.get("group_context", {})
    if not context or not context.get("available"):
        return

    rows = []
    outcome_labels = {"win": "胜", "draw": "平", "loss": "负"}
    for side, team_name in [("home", prediction["home_team"]), ("away", prediction["away_team"])]:
        team_context = context.get(side)
        if not team_context:
            continue
        scenarios = team_context.get("scenarios", {})
        for outcome in ["win", "draw", "loss"]:
            scenario = scenarios.get(outcome)
            if not scenario:
                continue
            rows.append(
                {
                    "球队": team_name,
                    "本场结果": outcome_labels[outcome],
                    "赛后积分": scenario["points"],
                    "预计排名": scenario["finish_label"],
                    "出线安全度": pct(float(scenario["qualification_score"])),
                    "潜在路径": scenario["opponent_hint"],
                }
            )

    st.markdown("**小组出线 / 淘汰赛路径修正**")
    st.write(f"- {context['summary']}")
    st.write(
        f"- 修正后预期进球倍率：{prediction['home_team']} "
        f"{context['lambda_multiplier']['home']:.2f}x，"
        f"{prediction['away_team']} {context['lambda_multiplier']['away']:.2f}x"
    )
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def usage_summary(status: pd.DataFrame) -> dict[str, str]:
    if status.empty:
        return {
            "updated": "暂无",
            "remaining": "未知",
            "used": "未知",
            "last_cost": "未知",
            "runs_left": "未知",
            "suggestion": "尚未成功拉取 The Odds API。",
        }
    row = status.iloc[0]
    headers = row.get("usage_headers", {})
    if isinstance(headers, str):
        headers = {}
    remaining = headers.get("x-requests-remaining")
    used = headers.get("x-requests-used")
    last_cost = headers.get("x-requests-last")
    if remaining is not None and last_cost not in (None, "0", 0):
        runs_left = str(int(float(remaining) // float(last_cost)))
    else:
        runs_left = "未知"
    rows = int(row.get("rows", 0) or 0)
    error = str(row.get("error", "") or "").strip()
    if error:
        suggestion = f"The Odds API 已尝试请求但返回错误：{error}"
    elif rows <= 0 and headers:
        suggestion = "The Odds API 已接通并消耗额度，但本次没有匹配到当前赛程盘口，页面暂用本地样例盘口。"
    elif rows > 0:
        suggestion = "The Odds API 已接通。云端按北京时间 14:00 和 19:00 两个档位刷新，其他刷新使用缓存保护额度。"
    else:
        suggestion = "尚未成功拉取 The Odds API。"
    return {
        "updated": str(row.get("fetched_at_utc", "暂无")),
        "remaining": str(remaining or "未知"),
        "used": str(used or "未知"),
        "last_cost": str(last_cost or "未知"),
        "runs_left": runs_left,
        "suggestion": suggestion,
    }


def render_status_band(odds_source: str, status: pd.DataFrame) -> None:
    summary = usage_summary(status)
    source_label = "The Odds API live 快照" if odds_source == "odds_live.csv" else "本地样例盘口"
    st.markdown(
        f"""
        <div class="status-band">
            <strong>盘口数据源：</strong>{source_label}<br>
            <strong>最近更新：</strong>{summary['updated']}<br>
            <strong>额度：</strong>剩余 {summary['remaining']}，已用 {summary['used']}，本次消耗 {summary['last_cost']}，按当前请求大约还能更新 {summary['runs_left']} 次。<br>
            <strong>更新频率：</strong>{summary['suggestion']}
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data
def cached_data(
    cache_version: str,
    api_key: str | None,
    update_slot: str,
) -> dict[str, pd.DataFrame]:
    _ = cache_version
    _ = update_slot
    return load_data(api_key=api_key)


def schedule_view(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["北京时间", "比赛", "分组", "场地", "状态"])

    view = frame.copy()
    view["比赛"] = view["home_team"] + " vs " + view["away_team"]
    view["比分"] = view.apply(
        lambda row: (
            f"{int(row['home_score'])}-{int(row['away_score'])}"
            if pd.notna(row["home_score"]) and pd.notna(row["away_score"])
            else "未赛"
        ),
        axis=1,
    )
    view["状态"] = view.apply(
        lambda row: "完场 " + row["比分"] if row["status"] == "FT" else "待赛",
        axis=1,
    )
    return view[["kickoff_cn", "比赛", "group", "venue", "状态"]].rename(
        columns={"kickoff_cn": "北京时间", "group": "分组", "venue": "场地"}
    )


def render_match_card(
    match: pd.Series,
    prediction: dict[str, object],
    odds: pd.DataFrame,
    min_edge: float,
) -> None:
    home = prediction["home_team"]
    away = prediction["away_team"]
    final_probability = prediction["final_probability"]
    top_scores = prediction["top_scores"]
    factors = prediction["factors"]
    actual_score = ""
    if pd.notna(match.get("home_score")) and pd.notna(match.get("away_score")):
        actual_score = f"{int(match['home_score'])}-{int(match['away_score'])}"

    with st.container(border=True):
        title_left, title_right = st.columns([1.5, 1])
        with title_left:
            st.markdown(f"<span class='match-chip'>{match['group']}</span>", unsafe_allow_html=True)
            st.subheader(f"{home} vs {away}")
            st.caption(f"{match['group']} | {match['kickoff_cn']} 北京时间 | {match['venue']}")
        with title_right:
            status = "已完场" if match["status"] == "FT" else "待赛"
            st.metric("赛程状态", status)
            if actual_score:
                st.metric("实际比分", actual_score)

        prob_cols = st.columns(3)
        prob_cols[0].metric(f"{home}胜", pct(final_probability["home"]))
        prob_cols[1].metric("平局", pct(final_probability["draw"]))
        prob_cols[2].metric(f"{away}胜", pct(final_probability["away"]))

        body_left, body_right = st.columns([1.15, 1])
        with body_left:
            xg_cols = st.columns(2)
            xg_cols[0].metric(f"{home}预期进球", f"{prediction['lambda_home']:.2f}")
            xg_cols[1].metric(f"{away}预期进球", f"{prediction['lambda_away']:.2f}")

            st.markdown("**预测比分**")
            render_score_list(top_scores.head(5))
            index_cols = st.columns(2)
            with index_cols[0]:
                render_index_box("冷门指数", prediction["upset"], "index-fill-upset")
            with index_cols[1]:
                render_index_box("大比分指数", prediction["big_score"], "index-fill-goals")
            render_bet_box(
                odds[odds["match_id"] == prediction["match_id"]],
                prediction,
                min_edge,
            )

        with body_right:
            st.markdown("**可能影响因素**")
            if factors.empty:
                st.write("暂无影响因素数据")
            else:
                for _, row in factors.head(6).iterrows():
                    sign = "+" if row["impact"] == "positive" else "-"
                    st.write(f"{sign} {row['team']}：{row['description']}")

            st.markdown("**盘口流 / 战术克制**")
            for flag in prediction["market_flow_flags"][:2]:
                st.write(f"- {flag}")
            st.write(f"- {prediction['matchup_summary']}")
            render_group_context(prediction)

        with st.expander("查看7层模型拆解和比分矩阵"):
            breakdown = pd.DataFrame(
                [
                    {
                        "来源": "ELO/贝叶斯",
                        home: pct(prediction["elo_probability"]["home"]),
                        "平局": pct(prediction["elo_probability"]["draw"]),
                        away: pct(prediction["elo_probability"]["away"]),
                    },
                    {
                        "来源": "赔率去水",
                        home: pct(prediction["odds_probability"]["home"]),
                        "平局": pct(prediction["odds_probability"]["draw"]),
                        away: pct(prediction["odds_probability"]["away"]),
                    },
                    {
                        "来源": "外部模型",
                        home: pct(prediction["external_probability"]["home"]),
                        "平局": pct(prediction["external_probability"]["draw"]),
                        away: pct(prediction["external_probability"]["away"]),
                    },
                    {
                        "来源": "xG",
                        home: pct(prediction["xg_probability"]["home"]),
                        "平局": pct(prediction["xg_probability"]["draw"]),
                        away: pct(prediction["xg_probability"]["away"]),
                    },
                    {
                        "来源": "盘口流",
                        home: pct(prediction["market_flow_probability"]["home"]),
                        "平局": pct(prediction["market_flow_probability"]["draw"]),
                        away: pct(prediction["market_flow_probability"]["away"]),
                    },
                    {
                        "来源": "融合后",
                        home: pct(prediction["base_probability"]["home"]),
                        "平局": pct(prediction["base_probability"]["draw"]),
                        away: pct(prediction["base_probability"]["away"]),
                    },
                    {
                        "来源": "市场修正后",
                        home: pct(prediction["market_adjusted_probability"]["home"]),
                        "平局": pct(prediction["market_adjusted_probability"]["draw"]),
                        away: pct(prediction["market_adjusted_probability"]["away"]),
                    },
                    {
                        "来源": "出线路径修正后",
                        home: pct(prediction["final_probability"]["home"]),
                        "平局": pct(prediction["final_probability"]["draw"]),
                        away: pct(prediction["final_probability"]["away"]),
                    },
                ]
            )
            st.dataframe(breakdown, use_container_width=True, hide_index=True)

            matrix = prediction["score_matrix"].copy() * 100
            fig = px.imshow(
                matrix,
                labels=dict(x=f"{away}进球", y=f"{home}进球", color="概率%"),
                color_continuous_scale="RdYlGn",
                aspect="auto",
            )
            fig.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig, use_container_width=True)

        with st.expander("查看赛前叙事报告：易经 / 塔罗"):
            score_candidates = [str(row["score"]) for _, row in top_scores.head(3).iterrows()]
            narrative_report = build_narrative_report(
                str(home),
                str(away),
                match.get("kickoff_utc", match.get("kickoff_cn", "")),
                score_candidates=score_candidates,
            )
            render_narrative_report(narrative_report)


def render_monitoring(
    *,
    odds: pd.DataFrame,
    odds_history: pd.DataFrame,
    predictions: list[dict[str, object]],
    min_edge: float,
    min_move_pct: float,
) -> None:
    st.markdown("### 盘口监控")
    value_bets = combined_value_bets(odds, predictions, min_edge=min_edge)
    change_frame = odds_change_summary(odds_history, min_abs_move_pct=min_move_pct)

    left, right = st.columns(2)
    with left:
        st.markdown("**Value bet 自动提醒**")
        if value_bets.empty:
            st.info("当前没有达到阈值的 value bet。")
        else:
            view = value_bets.copy()
            view["模型概率"] = view["model_probability"].map(pct)
            view["市场概率"] = view["market_probability"].map(pct)
            view["概率差"] = view["probability_gap"].map(pct)
            view["Edge"] = view["edge"].map(pct)
            view["赔率"] = view["odds"].map(lambda value: f"{value:.2f}")
            st.dataframe(
                view[
                    [
                        "match",
                        "bookmaker",
                        "outcome_label",
                        "赔率",
                        "模型概率",
                        "市场概率",
                        "概率差",
                        "Edge",
                    ]
                ].rename(
                    columns={
                        "match": "比赛",
                        "bookmaker": "公司",
                        "outcome_label": "方向",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

    with right:
        st.markdown("**赔率变化提醒**")
        if change_frame.empty:
            st.info("暂无达到阈值的赔率变化。运行多次 `scripts/update_odds.py` 后会形成历史。")
        else:
            view = change_frame.copy()
            view["变化"] = view["move_pct"].map(lambda value: f"{value:+.1f}%")
            view["旧赔率"] = view["old_odds"].map(lambda value: f"{value:.2f}")
            view["新赔率"] = view["new_odds"].map(lambda value: f"{value:.2f}")
            st.dataframe(
                view[
                    [
                        "match_id",
                        "bookmaker",
                        "outcome_label",
                        "direction",
                        "旧赔率",
                        "新赔率",
                        "变化",
                    ]
                ].rename(
                    columns={
                        "match_id": "比赛ID",
                        "bookmaker": "公司",
                        "outcome_label": "方向",
                        "direction": "方向变化",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )


st.set_page_config(page_title="世界杯今日预测", layout="wide")
st.title("世界杯今日预测")

odds_api_key = secret_value("THE_ODDS_API_KEY")
data = cached_data(DATA_CACHE_VERSION, odds_api_key, odds_update_slot())
required_keys = {
    "matches",
    "team_stats",
    "odds",
    "factors",
    "external_predictions",
    "xg_inputs",
    "team_form",
    "matchup_factors",
    "past_results",
    "worldcup_schedule",
    "group_standings",
    "odds_source",
    "odds_history",
    "odds_api_status",
}
if not required_keys.issubset(data):
    st.cache_data.clear()
    data = load_data(api_key=odds_api_key)
if "knockout_paths" not in data:
    data["knockout_paths"] = pd.DataFrame()

matches = data["matches"]
schedule = data["worldcup_schedule"]
if "matchday_date" not in schedule.columns:
    schedule["matchday_date"] = schedule["fixture_date_utc"]
else:
    schedule["matchday_date"] = schedule["matchday_date"].fillna(schedule["fixture_date_utc"])
odds_source = str(data["odds_source"].iloc[0]["source"])
today_cn = datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()

inject_style()

st.sidebar.header("模型设置")
prediction_days = sorted(schedule["matchday_date"].dropna().unique())
scheduled_days = sorted(
    schedule.loc[schedule["status"].ne("FT"), "matchday_date"].dropna().unique()
)
if scheduled_days:
    default_prediction_day = scheduled_days[-1]
elif today_cn in set(prediction_days):
    default_prediction_day = today_cn
else:
    default_prediction_day = prediction_days[-1]
prediction_day = st.sidebar.selectbox(
    "预测赛程日",
    options=prediction_days,
    index=prediction_days.index(default_prediction_day),
)
elo_weight = st.sidebar.slider("ELO权重", 0.0, 1.0, 0.22, 0.01)
odds_weight = st.sidebar.slider("赔率权重", 0.0, 1.0, 0.30, 0.01)
external_weight = st.sidebar.slider("外部模型权重", 0.0, 1.0, 0.16, 0.01)
xg_weight = st.sidebar.slider("xG权重", 0.0, 1.0, 0.22, 0.01)
market_flow_weight = st.sidebar.slider("盘口流权重", 0.0, 1.0, 0.10, 0.01)
market_bias_k = st.sidebar.slider("市场情绪修正 k", 0.0, 5.0, 2.0, 0.1)
value_edge = st.sidebar.slider("Value bet Edge阈值", 0.0, 0.2, 0.03, 0.01)
move_threshold = st.sidebar.slider("赔率变化提醒阈值", 1.0, 20.0, 3.0, 0.5)
simulations = st.sidebar.select_slider(
    "蒙特卡洛次数",
    options=[10000, 25000, 50000, 100000],
    value=10000,
)

config = PredictionConfig(
    elo_weight=elo_weight,
    odds_weight=odds_weight,
    external_weight=external_weight,
    xg_weight=xg_weight,
    market_flow_weight=market_flow_weight,
    market_bias_k=market_bias_k,
    simulations=simulations,
)

fixture_matches = schedule[schedule["matchday_date"] == prediction_day].sort_values("kickoff_utc")
local_matches = schedule[schedule["local_date_cn"] == today_cn].sort_values("kickoff_utc")

st.markdown(f"### 赛程日 {prediction_day} 的比赛预测")
render_status_band(odds_source, data["odds_api_status"])
st.caption("下方预测融合赔率、外部模型、xG、贝叶斯状态、盘口流和 Dixon-Coles 比分修正。")

available_fixture = fixture_matches.merge(
    matches[["match_id", "neutral_site", "notes"]],
    on="match_id",
    how="inner",
)

predictions: list[dict[str, object]] = []
for _, fixture in available_fixture.iterrows():
    match_row = pd.Series(
        {
            "match_id": fixture["match_id"],
            "group": fixture["group"],
            "home_team": fixture["home_team"],
            "away_team": fixture["away_team"],
            "neutral_site": bool(fixture["neutral_site"]),
            "notes": fixture["notes"],
        }
    )
    prediction = predict_match(
        match=match_row,
        team_stats=data["team_stats"],
        odds=data["odds"],
        factors=data["factors"],
        external_predictions=data["external_predictions"],
        xg_inputs=data["xg_inputs"],
        team_form=data["team_form"],
        matchup_factors=data["matchup_factors"],
        past_results=data["past_results"],
        group_standings=data["group_standings"],
        knockout_paths=data["knockout_paths"],
        config=config,
        odds_source=odds_source,
    )
    predictions.append(prediction)
    render_match_card(fixture, prediction, data["odds"], value_edge)

render_monitoring(
    odds=data["odds"],
    odds_history=data["odds_history"],
    predictions=predictions,
    min_edge=value_edge,
    min_move_pct=move_threshold,
)

st.markdown("### 今日赛程")
tab_fixture, tab_local = st.tabs(["FIFA赛程日", "北京时间今日"])
with tab_fixture:
    st.dataframe(schedule_view(fixture_matches), use_container_width=True, hide_index=True)
with tab_local:
    st.dataframe(schedule_view(local_matches), use_container_width=True, hide_index=True)
