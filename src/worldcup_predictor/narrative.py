from __future__ import annotations

from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any


DATA_DIR = Path(__file__).resolve().parents[2] / "data"

TRIGRAM_LINES = {
    "乾": [1, 1, 1],
    "兑": [1, 1, 0],
    "离": [1, 0, 1],
    "震": [1, 0, 0],
    "巽": [0, 1, 1],
    "坎": [0, 1, 0],
    "艮": [0, 0, 1],
    "坤": [0, 0, 0],
}

TRIGRAM_ELEMENTS = {
    "乾": "金",
    "兑": "金",
    "离": "火",
    "震": "木",
    "巽": "木",
    "坎": "水",
    "艮": "土",
    "坤": "土",
}

ELEMENT_RELATIONS = {
    ("木", "火"): "生",
    ("火", "土"): "生",
    ("土", "金"): "生",
    ("金", "水"): "生",
    ("水", "木"): "生",
    ("木", "土"): "克",
    ("土", "水"): "克",
    ("水", "火"): "克",
    ("火", "金"): "克",
    ("金", "木"): "克",
}

MONTH_BRANCH_ELEMENTS = {
    1: ("丑", "土"),
    2: ("寅", "木"),
    3: ("卯", "木"),
    4: ("辰", "土"),
    5: ("巳", "火"),
    6: ("午", "火"),
    7: ("未", "土"),
    8: ("申", "金"),
    9: ("酉", "金"),
    10: ("戌", "土"),
    11: ("亥", "水"),
    12: ("子", "水"),
}

LINE_MEANINGS = {
    1: "底层动因正在形成，开局节奏和准备质量最重要",
    2: "中前段需要协作与纪律，谁先稳住结构谁更舒服",
    3: "比赛可能出现反复，临场调整会放大影响",
    4: "外部压力上升，替补、裁判尺度或场面变化更值得关注",
    5: "主导权进入核心球员和关键决策层，强弱势会被放大",
    6: "走势接近极点，后段风险、体能和情绪管理更关键",
}

LINE_TEXTS = {
    1: "初爻发动，事情起于底层。对应比赛就是开局试探、阵型落位和第一波压迫质量；若一方太急，容易在尚未站稳时露出空间。",
    2: "二爻发动，重在中前段的承接。对应比赛是中场协作、二点球和边后卫保护，谁能让体系不断线，谁就能先稳住局面。",
    3: "三爻发动，处在进退交界。对应比赛容易有反复，领先也未必稳，落后也未必散，临场调整和情绪控制会被放大。",
    4: "四爻发动，外部压力开始进入场内。对应比赛可能受换人、判罚尺度、观众情绪或战术冒险影响，走势不会太平顺。",
    5: "五爻发动，主位得势但不能妄动。对应比赛的关键在核心球员和主帅选择，越是强势方越要避免冒进。",
    6: "上爻发动，走势接近极点。对应比赛后段风险很高，体能、阵型距离和最后一次选择可能决定结果。",
}

TAROT_POSITIONS = [
    ("过去", 0.25),
    ("现在", 0.35),
    ("未来", 0.40),
]


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _seeded_rng(team_a: str, team_b: str, match_time: Any, salt: str) -> random.Random:
    seed_text = f"{match_time}|{team_a}|{team_b}|{salt}"
    digest = hashlib.sha256(seed_text.encode("utf-8")).hexdigest()
    return random.Random(int(digest[:16], 16))


def _hexagram_lines(hexagram: dict[str, Any]) -> list[int]:
    lower = TRIGRAM_LINES[str(hexagram["lower"])]
    upper = TRIGRAM_LINES[str(hexagram["upper"])]
    return lower + upper


def _match_month(match_time: Any) -> int:
    text = str(match_time)
    try:
        return int(text[5:7])
    except (ValueError, IndexError):
        return 6


def _element_relation(source: str, target: str) -> str:
    if source == target:
        return "比和"
    relation = ELEMENT_RELATIONS.get((source, target))
    if relation == "生":
        return "生"
    if relation == "克":
        return "克"
    reverse = ELEMENT_RELATIONS.get((target, source))
    if reverse == "生":
        return "被生"
    if reverse == "克":
        return "被克"
    return "无明显生克"


def _season_state(element: str, month_element: str) -> str:
    if element == month_element:
        return "旺"
    if ELEMENT_RELATIONS.get((month_element, element)) == "生":
        return "相"
    if ELEMENT_RELATIONS.get((element, month_element)) == "生":
        return "休"
    if ELEMENT_RELATIONS.get((element, month_element)) == "克":
        return "囚"
    if ELEMENT_RELATIONS.get((month_element, element)) == "克":
        return "死"
    return "平"


def _state_phrase(state: str) -> str:
    return {
        "旺": "旺相有力，表达顺畅",
        "相": "得令相助，执行力较稳",
        "休": "有泄气之象，力量不宜过度外放",
        "囚": "受环境牵制，推进会显得吃力",
        "死": "被月令压制，状态容易打折",
        "平": "不旺不衰，主要看临场细节",
    }[state]


def _relationship_sentence(team_a: str, team_b: str, relation: str) -> str:
    if relation == "比和":
        return f"体用比和，{team_a} 与 {team_b} 的叙事力量趋于接近，比赛更容易进入拉锯。"
    if relation == "生":
        return f"体卦生用卦，{team_a} 虽会主动投入，但也有为对手制造空间、攻势外泄之象。"
    if relation == "被生":
        return f"用卦生体卦，{team_a} 更容易借势展开，{team_b} 的动作反而可能成为其推进条件。"
    if relation == "克":
        return f"体卦克用卦，{team_a} 有压制 {team_b} 的意图，但能否压住要看体卦自身旺衰。"
    if relation == "被克":
        return f"用卦克体卦，{team_b} 对 {team_a} 的限制感更强，热门方容易踢得憋屈。"
    return "体用之间没有形成特别鲜明的生克，叙事重点应放在节奏和阶段变化。"


def _score_direction(narrative_score: float) -> str:
    if narrative_score >= 4:
        return "叙事比分方向：强势方赢面叙事较浓，倾向小胜到两球胜，但允许保留反向冷门分支。"
    if narrative_score >= 1:
        return "叙事比分方向：更像强势方小胜，若久攻不下也可能滑向平局或一球差。"
    if narrative_score <= -4:
        return "叙事比分方向：弱势方不败或制造冷门的叙事较强，可以给出偏离模型的爆冷比分。"
    if narrative_score <= -1:
        return "叙事比分方向：热门方会踢得不顺，倾向平局、弱势方不败，或强队非常艰难的小胜。"
    return "叙事比分方向：双方力量接近，倾向低比分拉锯，平局或一球差更符合叙事。"


def _score_list_text(score_candidates: list[str] | None) -> str:
    if not score_candidates:
        return ""
    return "量化模型的高频比分仅作概率参考：" + "、".join(score_candidates[:3]) + "。"


def _future_card_score(tarot: dict[str, Any]) -> float:
    for card in tarot.get("cards", []):
        if card.get("position") == "未来":
            return float(card.get("score", 0) or 0)
    return 0.0


def _narrative_score_candidates(
    team_a: str,
    team_b: str,
    match_time: Any,
    narrative_score: float,
    iching: dict[str, Any],
    tarot: dict[str, Any],
) -> list[dict[str, str]]:
    future_score = _future_card_score(tarot)
    volatile = (
        int(iching["changing_line"]) in {3, 4, 6}
        or abs(future_score) >= 3
        or str(iching["transformed_relation"]) in {"被克", "克"}
    )

    if narrative_score <= -4:
        selected = [
            ("0-1", "爆冷小胜", f"{team_b} 低位守住后偷到关键球"),
        ]
        if volatile:
            selected.append(("1-2", "反向剧情", f"{team_a} 压上后被 {team_b} 打出转换"))
    elif narrative_score <= -1:
        selected = [
            ("1-1", "平局冷门", "热门优势不顺，比赛被拖进消耗战"),
        ]
        if volatile:
            selected.append(("0-1", "低比分爆冷", f"{team_b} 依靠反击或定位球建立优势"))
    elif narrative_score < 1:
        selected = [
            ("1-1", "均势拉锯", "双方叙事力量接近，一球后仍可能回到平衡"),
        ]
        if volatile:
            selected.append(("0-0", "低节奏僵局", "前段试探过长，进球窗口被压缩"))
    elif narrative_score < 4:
        selected = [
            ("1-0", f"{team_a} 小胜", "主动方有优势但兑现效率一般"),
        ]
        if volatile:
            selected.append(("2-1", f"{team_a} 险胜", "优势方能进球，也会给对手反击窗口"))
    else:
        selected = [
            ("2-0", f"{team_a} 优势兑现", "主动方节奏和质量都能持续压制"),
        ]
        if volatile:
            selected.append(("3-1", "后段拉开", "领先后空间变大，比分可能被继续放大"))

    selected = selected[:2]
    return [
        {"score": score, "tag": tag, "reason": reason}
        for score, tag, reason in selected
    ]


def _narrative_score_text(narrative_scores: list[dict[str, str]]) -> str:
    if not narrative_scores:
        return ""
    items = [f"{item['score']}（{item['tag']}：{item['reason']}）" for item in narrative_scores[:2]]
    return (
        "叙事比分候选（仅保留1-2个，允许偏离量化模型）："
        + "；".join(items)
        + "。这些比分只用于赛前报告，不修改真实预测概率。"
    )


def _weak_state(state: str) -> bool:
    return state in {"休", "囚", "死"}


def _score_tendency(score: float, team_a: str, team_b: str) -> str:
    if score >= 2.5:
        return f"叙事倾向明显偏向 {team_a}，更适合写成主动进取、掌控节奏的一方。"
    if score >= 0.8:
        return f"叙事略偏向 {team_a}，但优势更多体现在势头和表达，不等于模型概率上升。"
    if score <= -2.5:
        return f"叙事倾向明显偏向 {team_b}，更适合写成反击、韧性或搅局的一方。"
    if score <= -0.8:
        return f"叙事略偏向 {team_b}，但只用于报告语气，不等于模型概率上升。"
    return "叙事信号接近均衡，更适合写成拉锯、谨慎和临场细节决定走势。"


@lru_cache(maxsize=1)
def load_hexagrams(path: Path = DATA_DIR / "hexagrams.json") -> list[dict[str, Any]]:
    hexagrams = json.loads(path.read_text(encoding="utf-8"))
    if len(hexagrams) != 64:
        raise ValueError(f"hexagrams.json must contain 64 hexagrams, got {len(hexagrams)}")
    line_patterns = [tuple(_hexagram_lines(item)) for item in hexagrams]
    if len(set(line_patterns)) != 64:
        raise ValueError("hexagrams.json must contain 64 unique upper/lower trigram patterns")
    return hexagrams


@lru_cache(maxsize=1)
def load_tarot_cards(path: Path = DATA_DIR / "tarot_cards.json") -> list[dict[str, Any]]:
    cards = json.loads(path.read_text(encoding="utf-8"))
    if len(cards) != 78:
        raise ValueError(f"tarot_cards.json must contain 78 cards, got {len(cards)}")
    names = [str(card["name"]) for card in cards]
    if len(set(names)) != 78:
        raise ValueError("tarot_cards.json must contain 78 unique cards")
    return cards


def iching_reading(team_a: str, team_b: str, match_time: Any) -> dict[str, Any]:
    hexagrams = load_hexagrams()
    rng = _seeded_rng(team_a, team_b, match_time, "iching")
    primary = rng.choice(hexagrams)
    changing_line = rng.randint(1, 6)

    primary_lines = _hexagram_lines(primary)
    transformed_lines = primary_lines.copy()
    transformed_lines[changing_line - 1] = 1 - transformed_lines[changing_line - 1]
    transformed = next(
        item for item in hexagrams if _hexagram_lines(item) == transformed_lines
    )

    primary_score = float(primary.get("score", 0))
    transformed_score = float(transformed.get("score", 0))
    line_shift = (changing_line - 3.5) * 0.12
    contribution = _clamp(primary_score * 0.62 + transformed_score * 0.38 + line_shift, -5, 5)
    tendency = _score_tendency(contribution, team_a, team_b)
    month = _match_month(match_time)
    month_branch, month_element = MONTH_BRANCH_ELEMENTS.get(month, ("午", "火"))
    body_trigram = str(primary["lower"])
    use_trigram = str(primary["upper"])
    transformed_use_trigram = str(transformed["upper"])
    body_element = TRIGRAM_ELEMENTS[body_trigram]
    use_element = TRIGRAM_ELEMENTS[use_trigram]
    transformed_use_element = TRIGRAM_ELEMENTS[transformed_use_trigram]
    body_state = _season_state(body_element, month_element)
    use_state = _season_state(use_element, month_element)
    transformed_use_state = _season_state(transformed_use_element, month_element)
    body_use_relation = _element_relation(body_element, use_element)
    transformed_relation = _element_relation(body_element, transformed_use_element)

    analysis = (
        f"本卦为{primary['name']}，五行属{primary['element']}，关键词是"
        f"{'、'.join(primary['keywords'])}。第{changing_line}爻动，"
        f"{LINE_MEANINGS[changing_line]}；变卦为{transformed['name']}，提示后续走势"
        f"{transformed['explanation']} 比赛倾向：{tendency}"
    )

    return {
        "hexagram": primary["name"],
        "changing_line": changing_line,
        "transformed": transformed["name"],
        "analysis": analysis,
        "primary_explanation": primary["explanation"],
        "transformed_explanation": transformed["explanation"],
        "match_tendency": tendency,
        "keywords": primary["keywords"],
        "element": primary["element"],
        "body_trigram": body_trigram,
        "use_trigram": use_trigram,
        "transformed_use_trigram": transformed_use_trigram,
        "body_element": body_element,
        "use_element": use_element,
        "transformed_use_element": transformed_use_element,
        "month_branch": month_branch,
        "month_element": month_element,
        "body_state": body_state,
        "use_state": use_state,
        "transformed_use_state": transformed_use_state,
        "body_use_relation": body_use_relation,
        "transformed_relation": transformed_relation,
        "line_text": LINE_TEXTS[changing_line],
        "score": round(contribution, 2),
    }


def tarot_reading(team_a: str, team_b: str, match_time: Any) -> dict[str, Any]:
    cards = load_tarot_cards()
    rng = _seeded_rng(team_a, team_b, match_time, "tarot")
    selected = rng.sample(cards, 3)

    readings = []
    weighted_score = 0.0
    for (position, weight), card in zip(TAROT_POSITIONS, selected):
        upright = rng.random() >= 0.5
        orientation = "正位" if upright else "逆位"
        keywords_key = "upright_keywords" if upright else "reversed_keywords"
        keywords = list(card[keywords_key])
        orientation_meaning = str(
            card["upright_meaning"] if upright else card["reversed_meaning"]
        )
        signed_score = float(card.get("score", 0))
        if not upright:
            signed_score = -signed_score
        weighted_score += signed_score * weight
        lean = _score_tendency(signed_score, team_a, team_b)
        interpretation = (
            f"{position}抽到{card['name']}（{orientation}），关键词是"
            f"{'、'.join(keywords)}。{card['meaning']} {orientation_meaning}"
            f"{card['match_context']} {lean}"
        )
        readings.append(
            {
                "position": position,
                "name": card["name"],
                "orientation": orientation,
                "keywords": keywords,
                "meaning": card["meaning"],
                "orientation_meaning": orientation_meaning,
                "match_context": card["match_context"],
                "lean": lean,
                "interpretation": interpretation,
                "score": round(_clamp(signed_score, -5, 5), 2),
            }
        )

    score = _clamp(weighted_score, -5, 5)
    timeline = "；".join(
        f"{card['position']}为{card['name']}（{card['orientation']}），主{card['keywords'][0]}"
        for card in readings
    )
    if score >= 1:
        synthesis = (
            f"塔罗三张牌连成的走势偏向 {team_a}：过去的背景、现在的场面和未来的落点，"
            "更像是强势方能把节奏慢慢收回到自己脚下。"
        )
    elif score <= -1:
        synthesis = (
            f"塔罗三张牌连成的走势偏向 {team_b} 或平衡局：比赛不会顺着纸面强弱轻松展开，"
            "更像是被拖慢、被消耗，后段仍有变数。"
        )
    else:
        synthesis = "塔罗三张牌整体接近中性，提示比赛发展不会单线推进，而是拉锯、修正、再拉锯。"

    return {
        "cards": readings,
        "score": round(score, 2),
        "analysis": _score_tendency(score, team_a, team_b),
        "timeline": timeline,
        "synthesis": synthesis,
    }


def build_match_summary(
    team_a: str,
    team_b: str,
    iching: dict[str, Any],
    tarot: dict[str, Any],
    narrative_score: float,
    score_candidates: list[str] | None = None,
    narrative_scores: list[dict[str, str]] | None = None,
) -> str:
    body_weak = _weak_state(str(iching["body_state"]))
    use_strong = str(iching["use_state"]) in {"旺", "相"}
    relation_text = str(iching["body_use_relation"])
    transformed_relation_text = str(iching["transformed_relation"])
    blocked_attack = body_weak and relation_text in {"比和", "生", "克"}
    use_pressure = use_strong or relation_text in {"被克", "比和"}

    if blocked_attack or narrative_score <= 1.0:
        opening_pace = (
            f"上半场更可能偏谨慎，{team_a} 即使拥有更多控球和纸面主动，也不容易快速打穿 {team_b} 的防线"
        )
    else:
        opening_pace = (
            f"上半场 {team_a} 更容易抢到主动，比赛有较早进入高压区的倾向"
        )

    if transformed_relation_text in {"比和", "被克"} or narrative_score <= 1.0:
        late_pace = (
            "后半程会进入互有攻防和体能消耗，比分若迟迟打不开，平局权重会在叙事上升高"
        )
    else:
        late_pace = (
            "后半程如果领先方能稳住结构，优势会继续累积，但过度压上仍有反击风险"
        )
    risk = (
        f"对 {team_a} 而言，风险在于久攻不下后心态和阵型变形；对 {team_b} 而言，只要防守纪律不散，就有机会把比赛拖进自己想要的节奏。"
        if blocked_attack or use_pressure
        else f"对 {team_a} 而言，风险在于急于扩大优势导致攻守距离被拉长；对 {team_b} 而言，关键是守住前段压力并把反击质量打出来。"
    )
    relation = _relationship_sentence(team_a, team_b, str(iching["body_use_relation"]))
    transformed_relation = _relationship_sentence(
        team_a,
        team_b,
        str(iching["transformed_relation"]),
    )
    score_direction = _score_direction(narrative_score)
    score_text = _score_list_text(score_candidates)
    narrative_score_text = _narrative_score_text(narrative_scores or [])

    return (
        f"{team_a} vs {team_b}（{iching['hexagram']}变{iching['transformed']}）。"
        f"本卦下卦为{iching['body_trigram']}{iching['body_element']}，作为体卦看 {team_a} 的主动状态；"
        f"上卦为{iching['use_trigram']}{iching['use_element']}，作为用卦看 {team_b} 的应对与限制。"
        f"比赛时间落在{iching['month_branch']}月，月令五行为{iching['month_element']}："
        f"体卦处「{iching['body_state']}」地，{_state_phrase(str(iching['body_state']))}；"
        f"用卦处「{iching['use_state']}」地，{_state_phrase(str(iching['use_state']))}。"
        f"{relation}"
        f"因此本场不是单纯纸面实力碾压的叙事，而要看主动方的进攻能否持续兑现。"
        f"动爻为第{iching['changing_line']}爻，{iching['line_text']} "
        f"变卦后用卦化为{iching['transformed_use_trigram']}{iching['transformed_use_element']}，"
        f"处「{iching['transformed_use_state']}」地，{transformed_relation}"
        f"塔罗三张牌给出的阶段线是：{tarot['timeline']}。{tarot['synthesis']}"
        f"综合来看，{opening_pace}；{late_pace}。{risk}"
        f"{score_direction}{narrative_score_text}{score_text}"
    )


def build_narrative_report(
    team_a: str,
    team_b: str,
    match_time: Any,
    score_candidates: list[str] | None = None,
) -> dict[str, Any]:
    iching = iching_reading(team_a, team_b, match_time)
    tarot = tarot_reading(team_a, team_b, match_time)
    narrative_score = _clamp(float(iching["score"]) + float(tarot["score"]), -10, 10)
    narrative_scores = _narrative_score_candidates(
        team_a,
        team_b,
        match_time,
        narrative_score,
        iching,
        tarot,
    )
    summary = build_match_summary(
        team_a,
        team_b,
        iching,
        tarot,
        narrative_score,
        score_candidates,
        narrative_scores,
    )
    return {
        "narrative_score": round(narrative_score, 2),
        "iching_contribution": iching["score"],
        "tarot_contribution": tarot["score"],
        "narrative_scores": narrative_scores,
        "iching": iching,
        "tarot": tarot,
        "summary": summary,
        "score_direction": _score_direction(narrative_score),
        "notice": "易经和塔罗只用于生成赛前叙事报告，不参与真实预测模型概率计算。",
    }
