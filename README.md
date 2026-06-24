# 世界杯预测 MVP

这个项目实现了一个可运行的世界杯预测首页，核心是 7 层预测系统：

```text
1. ELO：基础实力
2. Odds：赔率去水后的市场概率
3. External Models：外部模型预测源
4. xG：射门质量、射门位置、防守压力、快攻/阵地
5. Dixon-Coles：低比分相关修正
6. Bayesian Update：赛后动态实力/状态更新
7. Monte Carlo：重复模拟得到最终分布
```

核心公式：

```text
P_base = normalize(
  w1 * ELOProbability +
  w2 * OddsProbability +
  w3 * ExternalModelProbability +
  w4 * xGProbability +
  w5 * MarketFlowProbability
)

P_final = normalize(P_base * (1 + k * market_bias))

lambda = f(shot_quality, shot_location, defensive_pressure, transition_attack)

P(x, y) = Poisson(x) * Poisson(y) * rho(x, y)
rho = 1 - alpha * exp(-beta * (x + y))

simulate 10000-100000 matches -> final distribution
```

## 数据文件

- `data/matches.csv`：比赛列表
- `data/team_stats.csv`：球队 Elo、进攻强度、防守系数
- `data/odds.csv`：多家公司初盘和即时盘
- `data/factors.csv`：影响因素展示文案
- `data/external_predictions.csv`：外部模型预测源
- `data/xg_inputs.csv`：射门质量、位置、防守压力、转换进攻等 xG 输入
- `data/team_form.csv`：贝叶斯状态更新输入
- `data/matchup_factors.csv`：战术克制系数
- `data/past_results.csv`：赛后 Bayesian ELO 更新样本

`odds.csv` 使用十进制赔率。程序会先把各家公司胜平负赔率转成隐含概率，再去除水位并求平均。

## 启动

```powershell
pip install -r requirements.txt
streamlit run app.py
```

## 接入 The Odds API

优先使用结构化 API，再统一标准化成本地模型表：

```powershell
$env:THE_ODDS_API_KEY="你的key"
python scripts/update_odds.py
```

手动定时更新：

```powershell
$env:THE_ODDS_API_KEY="你的key"
python scripts/watch_odds.py --interval-minutes 15
```

目前请求 `h2h,spreads,totals`，The Odds API 返回显示每次消耗 3 个额度。500 额度大约可以更新 166 次：

- 每 5 分钟一次：约 13.8 小时
- 每 10 分钟一次：约 27.7 小时
- 每 15 分钟一次：约 41.5 小时
- 每 30 分钟一次：约 83 小时

脚本会请求：

```text
sport=soccer_fifa_world_cup
regions=eu
markets=h2h,spreads,totals
oddsFormat=decimal
```

输出文件：

- `data/odds_live.csv`：模型实际优先读取的标准化盘口
- `data/odds_api_status.json`：请求时间、额度响应头、未匹配比赛
- `data/odds_raw/`：原始 JSON 快照

如果没有 `odds_live.csv`，程序会自动回退到 `data/odds.csv` 样例盘口。

## 盘口变化监控和 Value Bet

每次成功运行 `scripts/update_odds.py` 后，脚本会追加一份历史快照到：

```text
data/odds_history.csv
```

首页会自动展示两类提醒：

- 赔率变化提醒：同一比赛、同一公司、同一方向的赔率变化超过阈值
- Value bet 自动提醒：`edge = 模型概率 * 当前赔率 - 1`

侧边栏可以调整：

- `Value bet Edge阈值`
- `赔率变化提醒阈值`

提醒只代表模型和市场赔率存在差异，不代表确定收益。

盘口流说明：

- 使用 `data/odds.csv` 时，盘口流只是基于样例初盘/当前盘的演示信号
- 使用 `data/odds_live.csv` 且多次运行 `scripts/update_odds.py` 后，盘口流和赔率变化提醒才会基于真实 API 快照历史

## 下一步

- 接入赔率 API 或合规公开数据源
- 接入外部模型预测的自动抓取/导入任务
- 用真实 xG 数据校准 `shot_quality`、`shot_location`、`defensive_pressure`
- 做完整世界杯赛程模拟，输出小组出线、晋级、冠军概率
- 给影响因素增加数值化 impact，自动修正 xG 和战术系数
