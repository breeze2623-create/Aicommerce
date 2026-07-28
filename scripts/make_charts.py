#!/usr/bin/env python3
"""AI 电商行业研究 - 图表样张生成脚本。

用法：python3 scripts/make_charts.py
数据：data/*.csv（更新数据后重跑本脚本即可刷新 charts/*.png）
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "charts"
OUT.mkdir(exist_ok=True)

# 中文字体（云端 Linux 环境预装文泉驿微米黑）
plt.rcParams["font.sans-serif"] = ["WenQuanYi Micro Hei", "Droid Sans Fallback", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 150
plt.rcParams["savefig.bbox"] = "tight"
plt.rcParams["axes.edgecolor"] = "#9CA3AF"
plt.rcParams["axes.linewidth"] = 0.8

C_BLUE = "#2563EB"   # 海外 / 主色
C_RED = "#DC2626"    # 国内
C_GREEN = "#059669"
C_AMBER = "#D97706"
C_GRAY = "#6B7280"
C_LIGHT = "#93C5FD"


def footer(fig, text):
    fig.text(0.01, -0.02, text, fontsize=7.5, color=C_GRAY, ha="left", va="top")


def chart_01_global_forecasts():
    df = pd.read_csv(DATA / "global_market_forecasts.csv")
    df["mid"] = (df["低值_十亿美元"] + df["高值_十亿美元"]) / 2
    df = df.sort_values("mid")
    labels = [
        f"{r.机构}｜{r.范围} {r.目标年份}" for r in df.itertuples()
    ]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    colors = [C_BLUE if r.范围 == "美国" else C_AMBER for r in df.itertuples()]
    for i, r in enumerate(df.itertuples()):
        lo, hi = r.低值_十亿美元, r.高值_十亿美元
        if lo == hi:
            ax.barh(i, lo, height=0.55, color=colors[i], alpha=0.9)
            ax.text(hi * 1.06, i, f"${hi:,.0f}B", va="center", fontsize=9)
        else:
            ax.barh(i, hi - lo, left=lo, height=0.55, color=colors[i], alpha=0.9)
            ax.text(hi * 1.06, i, f"${lo:,.0f}~{hi:,.0f}B", va="center", fontsize=9)
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(labels, fontsize=9.5)
    ax.set_xscale("log")
    ax.set_xlim(100, 12000)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.set_xlabel("市场规模预测（十亿美元，对数轴）", fontsize=9)
    ax.set_title("代理式商务（Agentic Commerce）规模预测：机构口径相差 35 倍\n——差异源于『AI 平台内成交』到『AI 编排/影响的零售收入』的口径谱系", fontsize=11, loc="left")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=C_BLUE, label="美国口径"), Patch(color=C_AMBER, label="全球口径")], loc="lower right", fontsize=9, frameon=False)
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    footer(fig, "来源：eMarketer / Morgan Stanley / Bain / McKinsey / Edgar Dunn 公开预测（2025-10~2025-12 发布）。对照项：Gartner 预测 2028 年 >15 万亿美元 B2B 采购由 AI 代理中介（未画入）。整理：AI 电商研究计划，2026-07。")
    fig.savefig(OUT / "01_global_agentic_forecasts.png")
    plt.close(fig)


def chart_02_us_ai_traffic():
    df = pd.read_csv(DATA / "adobe_ai_traffic.csv")
    per = df[df.panel == "period"]
    ind = df[df.panel == "industry"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    b1 = ax1.bar(per["标签"], per["同比增速_pct"], color=[C_LIGHT, C_BLUE, C_LIGHT, C_LIGHT], width=0.6)
    ax1.bar_label(b1, fmt="+%g%%", fontsize=9.5, padding=2)
    ax1.set_title("美国零售网站 AI 来源流量同比增速", fontsize=10.5, loc="left")
    ax1.set_ylabel("同比增速（%）", fontsize=9)
    ax1.tick_params(axis="x", labelsize=8.5, rotation=12)
    ax1.grid(axis="y", linestyle=":", alpha=0.5)
    ax1.set_ylim(0, 1350)

    ind = ind.sort_values("同比增速_pct")
    b2 = ax2.barh(ind["标签"], ind["同比增速_pct"], color=[C_GRAY, C_GRAY, C_GRAY, C_GRAY, C_RED], height=0.55)
    ax2.bar_label(b2, fmt="+%g%%", fontsize=9.5, padding=3)
    ax2.set_title("2026Q1 各行业 AI 流量增速：零售遥遥领先", fontsize=10.5, loc="left")
    ax2.set_xlabel("同比增速（%）", fontsize=9)
    ax2.set_xlim(0, 480)
    ax2.grid(axis="x", linestyle=":", alpha=0.5)
    fig.suptitle("生成式 AI 正在成为零售网站的结构性流量来源（图表 C2）", fontsize=12, x=0.01, ha="left")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    footer(fig, "来源：Adobe Digital Insights（基于美国零售网站超 1 万亿次访问），2026-04 发布；TechCrunch / PYMNTS 交叉验证。整理：AI 电商研究计划，2026-07。")
    fig.savefig(OUT / "02_us_ai_traffic_growth.png")
    plt.close(fig)


def chart_03_conversion_reversal():
    df = pd.read_csv(DATA / "conversion_metrics.csv")
    rev = df[df.panel == "reversal"]
    eng = df[df.panel == "engagement"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1.35, 1]})

    conv = rev[rev["指标"].str.contains("转化率")]
    rpv = rev[rev["指标"].str.contains("RPV")]
    x = [0, 1]
    w = 0.32
    b1 = ax1.bar([i - w / 2 for i in x], conv["数值_pct"], width=w, color=C_BLUE, label="转化率差（AI vs 非 AI）")
    b2 = ax1.bar([i + w / 2 for i in x], rpv["数值_pct"], width=w, color=C_AMBER, label="单次访问收入差（AI vs 非 AI）")
    for b in (b1, b2):
        ax1.bar_label(b, fmt="%+g%%", fontsize=10, padding=2)
    ax1.axhline(0, color="#111827", linewidth=0.9)
    ax1.set_xticks(x)
    ax1.set_xticklabels(["2025 年 3 月", "2026 年 3 月"], fontsize=10)
    ax1.set_ylim(-80, 70)
    ax1.set_title("一年内的历史性逆转：AI 流量从『劣质流量』变为最优渠道", fontsize=10.5, loc="left")
    ax1.legend(fontsize=8.5, frameon=False, loc="lower right")
    ax1.grid(axis="y", linestyle=":", alpha=0.5)

    b3 = ax2.bar(eng["指标"], eng["数值_pct"], color=C_GREEN, width=0.5)
    ax2.bar_label(b3, fmt="+%g%%", fontsize=10, padding=2)
    ax2.set_title("2026-03：AI 来源访客参与度全面占优", fontsize=10.5, loc="left")
    ax2.set_ylabel("相对非 AI 来源（%）", fontsize=9)
    ax2.set_ylim(0, 60)
    ax2.grid(axis="y", linestyle=":", alpha=0.5)
    fig.suptitle("AI 导流质量逆转（图表 C3）", fontsize=12, x=0.01, ha="left")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    footer(fig, "来源：Adobe Digital Insights，2026-04。注：2025-03 RPV 原文口径为『非 AI 流量单访问收入比 AI 高 128%』，换算为 AI 相对非 AI 约 -56%。整理：AI 电商研究计划，2026-07。")
    fig.savefig(OUT / "03_ai_conversion_reversal.png")
    plt.close(fig)


def chart_04_entrance_scale():
    df = pd.read_csv(DATA / "assistant_scale.csv").sort_values("规模_亿")
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    colors = [C_RED if r == "国内" else C_BLUE for r in df["区域"]]
    bars = ax.barh(df["产品"], df["规模_亿"], color=colors, height=0.58, alpha=0.92)
    for bar, r in zip(bars, df.itertuples()):
        ax.text(bar.get_width() + 0.08, bar.get_y() + bar.get_height() / 2,
                f"{r.规模_亿:g} 亿（{r.口径}）", va="center", fontsize=8.6)
    ax.set_xlim(0, 12.2)
    ax.set_xlabel("用户/设备规模（亿）——口径各异，仅作量级对照", fontsize=9)
    ax.set_title("国内外 AI 购物入口规模对照（图表 C4）\n红=国内，蓝=海外；WAU/MAU/年度用户/设备数不可直接混比", fontsize=11, loc="left")
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    footer(fig, "来源：OpenAI 披露、QuestMobile（2026-06）、亚马逊/京东财报与发布会、公开报道。整理：AI 电商研究计划，2026-07。")
    fig.savefig(OUT / "04_ai_entrance_user_scale.png")
    plt.close(fig)


def chart_05_china_private():
    df = pd.read_csv(DATA / "china_ai_private_ecommerce.csv")
    fig, ax = plt.subplots(figsize=(9, 4.6))
    colors = [C_RED if s == "实际" else "#F87171" for s in df["性质"]]
    bars = ax.bar(df["年份"].astype(str), df["市场规模_万亿元"], color=colors, width=0.55)
    ax.bar_label(bars, fmt="%.2f", fontsize=9.5, padding=2)
    ax.set_ylabel("市场规模（万亿元）", fontsize=9)
    ax.set_ylim(0, 4.0)
    ax.set_title("中国 AI 私域电商市场规模与渗透率（2025 实际 + 2026–2030 预测，图表 C5）\n注意：口径为『私域电商』子集；全量『中国 AI 电商 GMV』尚无权威口径（研究需自建估算）", fontsize=10.5, loc="left")
    ax2 = ax.twinx()
    ax2.plot(df["年份"].astype(str), df["渗透率_pct"], color=C_BLUE, marker="o", linewidth=2, label="AI 渗透率（右轴）")
    for x_, y_ in zip(df["年份"].astype(str), df["渗透率_pct"]):
        ax2.annotate(f"{y_:.1f}%", (x_, y_), textcoords="offset points", xytext=(0, 8), fontsize=8.5, color=C_BLUE, ha="center")
    ax2.set_ylabel("渗透率（%）", fontsize=9, color=C_BLUE)
    ax2.set_ylim(0, 80)
    ax2.tick_params(axis="y", labelcolor=C_BLUE)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    footer(fig, "来源：网经社电子商务研究中心《2025 年度中国私域电商市场数据报告》（2026-05 发布，电数宝数据库）。深红=实际值，浅红=预测值。整理：AI 电商研究计划，2026-07。")
    fig.savefig(OUT / "05_china_ai_private_ecommerce.png")
    plt.close(fig)


def chart_06_holiday():
    df = pd.read_csv(DATA / "salesforce_holiday.csv")
    sales = df[df.panel == "sales"]
    growth = df[df.panel == "growth"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1.3, 1]})

    pairs = [("2025假日季\n(11.1–12.31)", 12900, 2620), ("Cyber Week\n(11.25–12.1)", 3366, 670)]
    x = range(len(pairs))
    w = 0.34
    b1 = ax1.bar([i - w / 2 for i in x], [p[1] for p in pairs], width=w, color=C_GRAY, label="全球线上销售总额")
    b2 = ax1.bar([i + w / 2 for i in x], [p[2] for p in pairs], width=w, color=C_BLUE, label="其中 AI 与 Agent 影响")
    ax1.bar_label(b1, fmt="{:,.0f}", fontsize=9)
    ax1.bar_label(b2, fmt="{:,.0f}", fontsize=9)
    for i, p in enumerate(pairs):
        ax1.annotate(f"占 {p[2]/p[1]*100:.0f}% 订单", (i + w / 2, p[2]), textcoords="offset points", xytext=(0, 16), ha="center", fontsize=9, color=C_BLUE, fontweight="bold")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels([p[0] for p in pairs], fontsize=9.5)
    ax1.set_ylabel("销售额（亿美元）", fontsize=9)
    ax1.set_title("2025 假日季：AI 与 Agent 影响 20% 全球零售订单", fontsize=10.5, loc="left")
    ax1.legend(fontsize=8.5, frameon=False)
    ax1.grid(axis="y", linestyle=":", alpha=0.5)

    b3 = ax2.bar(growth["标签"].str.replace("的零售商", "\n的零售商"), growth["数值"], color=[C_GREEN, C_GRAY], width=0.45)
    ax2.bar_label(b3, fmt="%.1f%%", fontsize=10.5)
    ax2.set_ylabel("2025 假日季销售同比增速（%）", fontsize=9)
    ax2.set_ylim(0, 8)
    ax2.set_title("部署自有品牌 Agent 的零售商增速快 59%", fontsize=10.5, loc="left")
    ax2.tick_params(axis="x", labelsize=9)
    ax2.grid(axis="y", linestyle=":", alpha=0.5)
    fig.suptitle("假日季 AI 影响力（Salesforce 口径：『AI 影响的销售』≠『AI 内成交』，图表 C6）", fontsize=12, x=0.01, ha="left")
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    footer(fig, "来源：Salesforce 2025 假日购物报告 / Cyber Week 报告（基于 15 亿+ 消费者购物数据）。另：假日季 Agent 自主执行动作 +142%，AI 流量转化率约为社交流量 9 倍。整理：AI 电商研究计划，2026-07。")
    fig.savefig(OUT / "06_holiday_ai_influence.png")
    plt.close(fig)


def chart_07_scorecard():
    df = pd.read_csv(DATA / "instore_ai_scorecard.csv").sort_values("数值_pct")
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    colors = [C_GREEN if c == "效果提升" else C_BLUE for c in df["类别"]]
    bars = ax.barh(df["指标"], df["数值_pct"], color=colors, height=0.58)
    for bar, r in zip(bars, df.itertuples()):
        ax.text(bar.get_width() + 4, bar.get_y() + bar.get_height() / 2, f"+{r.数值_pct:g}%", va="center", fontsize=9.5)
    ax.set_xlim(0, 245)
    ax.set_xlabel("提升幅度 / 同比增速（%）", fontsize=9)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=C_GREEN, label="效果提升（转化/增速溢价）"), Patch(color=C_BLUE, label="使用规模增长（YoY）")], fontsize=8.5, frameon=False, loc="lower right")
    ax.set_title("站内 AI 导购成绩单（图表 C7）\nRufus 2025 年带来约 120 亿美元增量年化销售；Walmart：LLM 内自有 Agent 插件转化≈自有站 70%，而平台代结账仅≈1/3", fontsize=10.5, loc="left")
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    footer(fig, "来源：亚马逊 2025Q3/Q4 财报电话会（公司口径）、Adobe（2026-03）、Shopify（2026-05）、Salesforce（2025 假日季）、京东 618 发布会（2026-05）。整理：AI 电商研究计划，2026-07。")
    fig.savefig(OUT / "07_instore_ai_scorecard.png")
    plt.close(fig)


if __name__ == "__main__":
    chart_01_global_forecasts()
    chart_02_us_ai_traffic()
    chart_03_conversion_reversal()
    chart_04_entrance_scale()
    chart_05_china_private()
    chart_06_holiday()
    chart_07_scorecard()
    print("已生成图表：")
    for p in sorted(OUT.glob("*.png")):
        print(" -", p.relative_to(ROOT))
