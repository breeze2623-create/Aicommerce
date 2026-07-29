#!/usr/bin/env python3
"""AI电商行业研究报告 — 正式版图表生成脚本。"""

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

plt.rcParams["font.sans-serif"] = ["WenQuanYi Micro Hei", "Droid Sans Fallback", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 150
plt.rcParams["savefig.bbox"] = "tight"
plt.rcParams["axes.edgecolor"] = "#9CA3AF"
plt.rcParams["axes.linewidth"] = 0.8

C_BLUE = "#1D4ED8"
C_RED = "#B91C1C"
C_GREEN = "#047857"
C_AMBER = "#B45309"
C_GRAY = "#4B5563"
C_LIGHT = "#93C5FD"


def footer(fig, text):
    fig.text(0.01, -0.03, text, fontsize=7.2, color=C_GRAY, ha="left", va="top", wrap=True)


def chart_01_global_forecasts():
    df = pd.read_csv(DATA / "global_market_forecasts.csv")
    df["mid"] = (df["低值_十亿美元"] + df["高值_十亿美元"]) / 2
    df = df.sort_values("mid")
    labels = [f"{r.机构}｜{r.范围} {r.目标年份}" for r in df.itertuples()]
    fig, ax = plt.subplots(figsize=(9.2, 4.8))
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
    ax.set_xlabel("预测规模（十亿美元，对数轴）", fontsize=9)
    ax.set_title("图1  代理式商务规模预测对比（不同机构口径差异显著）", fontsize=12, loc="left", fontweight="bold")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=C_BLUE, label="美国口径"), Patch(color=C_AMBER, label="全球口径")],
              loc="lower right", fontsize=9, frameon=False)
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    footer(fig,
           "数据来源：eMarketer、Morgan Stanley、Bain、McKinsey、Edgar Dunn 公开预测（2025年10月—12月发布）。\n"
           "口径说明：eMarketer仅统计AI平台内完成结账的交易；Morgan Stanley为代理自主执行的购买；Bain含代理发起/影响/完成的购买；"
           "McKinsey为代理编排的零售收入（含AI影响的决策）。地域与年份差异会进一步放大数值差距。\n"
           "编制：AI电商行业研究报告｜数据截至2026-07")
    fig.savefig(OUT / "01_global_agentic_forecasts.png")
    plt.close(fig)


def chart_02_us_ai_traffic():
    df = pd.read_csv(DATA / "adobe_ai_traffic.csv")
    per = df[df.panel == "period"]
    ind = df[df.panel == "industry"].sort_values("同比增速_pct")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.3))
    b1 = ax1.bar(per["标签"], per["同比增速_pct"], color=[C_LIGHT, C_BLUE, C_LIGHT, C_LIGHT], width=0.6)
    ax1.bar_label(b1, fmt="+%g%%", fontsize=9.5, padding=2)
    ax1.set_title("美国零售网站AI来源流量同比增速", fontsize=10.5, loc="left")
    ax1.set_ylabel("同比增速（%）", fontsize=9)
    ax1.tick_params(axis="x", labelsize=8.5, rotation=12)
    ax1.grid(axis="y", linestyle=":", alpha=0.5)
    ax1.set_ylim(0, 1350)

    b2 = ax2.barh(ind["标签"], ind["同比增速_pct"],
                  color=[C_GRAY, C_GRAY, C_GRAY, C_GRAY, C_RED], height=0.55)
    ax2.bar_label(b2, fmt="+%g%%", fontsize=9.5, padding=3)
    ax2.set_title("2026Q1各行业AI流量增速对比", fontsize=10.5, loc="left")
    ax2.set_xlabel("同比增速（%）", fontsize=9)
    ax2.set_xlim(0, 480)
    ax2.grid(axis="x", linestyle=":", alpha=0.5)
    fig.suptitle("图2  美国零售网站生成式AI导流增长", fontsize=12, x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(rect=[0, 0.04, 1, 0.92])
    footer(fig,
           "数据来源：Adobe Digital Insights《季度AI流量报告》（2026年4月发布）。\n"
           "口径说明：基于Adobe Analytics覆盖的美国零售网站超过1万亿次访问；AI来源流量指从ChatGPT、Gemini、Perplexity等生成式AI平台跳转至零售网站的访问。\n"
           "编制：AI电商行业研究报告｜数据截至2026-07")
    fig.savefig(OUT / "02_us_ai_traffic_growth.png")
    plt.close(fig)


def chart_03_conversion_reversal():
    df = pd.read_csv(DATA / "conversion_metrics.csv")
    rev = df[df.panel == "reversal"]
    eng = df[df.panel == "engagement"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.3), gridspec_kw={"width_ratios": [1.35, 1]})

    conv = rev[rev["指标"].str.contains("转化率")]
    rpv = rev[rev["指标"].str.contains("RPV")]
    x = [0, 1]
    w = 0.32
    b1 = ax1.bar([i - w / 2 for i in x], conv["数值_pct"], width=w, color=C_BLUE, label="转化率差（AI相对非AI）")
    b2 = ax1.bar([i + w / 2 for i in x], rpv["数值_pct"], width=w, color=C_AMBER, label="单次访问收入差（AI相对非AI）")
    for b in (b1, b2):
        ax1.bar_label(b, fmt="%+g%%", fontsize=10, padding=2)
    ax1.axhline(0, color="#111827", linewidth=0.9)
    ax1.set_xticks(x)
    ax1.set_xticklabels(["2025年3月", "2026年3月"], fontsize=10)
    ax1.set_ylim(-80, 70)
    ax1.set_title("AI流量质量一年内完成逆转", fontsize=10.5, loc="left")
    ax1.legend(fontsize=8.5, frameon=False, loc="lower right")
    ax1.grid(axis="y", linestyle=":", alpha=0.5)

    b3 = ax2.bar(eng["指标"], eng["数值_pct"], color=C_GREEN, width=0.5)
    ax2.bar_label(b3, fmt="+%g%%", fontsize=10, padding=2)
    ax2.set_title("2026年3月：AI来源访客参与度", fontsize=10.5, loc="left")
    ax2.set_ylabel("相对非AI来源（%）", fontsize=9)
    ax2.set_ylim(0, 60)
    ax2.grid(axis="y", linestyle=":", alpha=0.5)
    fig.suptitle("图3  AI导流质量变化：转化率与单次访问收入", fontsize=12, x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(rect=[0, 0.04, 1, 0.92])
    footer(fig,
           "数据来源：Adobe Digital Insights（2026年4月发布）。\n"
           "口径说明：转化率=访问中完成购买的比例；RPV=单次访问收入。正值表示AI来源优于非AI来源。"
           "2025年3月RPV原文为「非AI比AI高128%」，换算为AI相对非AI约-56%。\n"
           "编制：AI电商行业研究报告｜数据截至2026-07")
    fig.savefig(OUT / "03_ai_conversion_reversal.png")
    plt.close(fig)


def chart_04_entrance_scale():
    df = pd.read_csv(DATA / "assistant_scale.csv").sort_values("规模_亿")
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    colors = [C_RED if r == "国内" else C_BLUE for r in df["区域"]]
    bars = ax.barh(df["产品"], df["规模_亿"], color=colors, height=0.55, alpha=0.92)
    for bar, r in zip(bars, df.itertuples()):
        ax.text(bar.get_width() + 0.08, bar.get_y() + bar.get_height() / 2,
                f"{r.规模_亿:g}亿｜{r.口径}｜{r.时点}", va="center", fontsize=8.5)
    ax.set_xlim(0, 12.5)
    ax.set_xlabel("规模（亿）", fontsize=9)
    ax.set_title("图4  主要AI购物相关入口用户规模对照", fontsize=12, loc="left", fontweight="bold")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=C_RED, label="国内"), Patch(color=C_BLUE, label="海外")],
              loc="lower right", fontsize=9, frameon=False)
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    footer(fig,
           "数据来源：QuestMobile（豆包、千问，2026年6月）；OpenAI公开披露（ChatGPT WAU）；Google公开披露（Gemini MAU）；"
           "亚马逊2025Q4财报电话会（Rufus年度使用用户）；Perplexity公司披露。\n"
           "口径说明：WAU=周活跃用户，MAU=月活跃用户，Rufus为年度累计使用用户。不同口径不可直接横向比较，本图仅作量级对照。"
           "本图仅收录可追溯至第三方监测或公司财报/官方披露的数据。\n"
           "编制：AI电商行业研究报告｜数据截至2026-07")
    fig.savefig(OUT / "04_ai_entrance_user_scale.png")
    plt.close(fig)


def chart_05_china_private():
    df = pd.read_csv(DATA / "china_ai_private_ecommerce.csv")
    fig, ax = plt.subplots(figsize=(9, 4.6))
    colors = [C_RED if s == "实际" else "#F87171" for s in df["性质"]]
    bars = ax.bar(df["年份"].astype(str), df["市场规模_万亿元"], color=colors, width=0.55)
    ax.bar_label(bars, fmt="%.2f", fontsize=9.5, label_type="center", color="white", fontweight="bold")
    ax.set_ylabel("市场规模（万亿元）", fontsize=9)
    ax.set_ylim(0, 4.0)
    ax.set_title("图5  中国AI私域电商市场规模与渗透率（2025—2030）", fontsize=12, loc="left", fontweight="bold")
    ax2 = ax.twinx()
    ax2.plot(df["年份"].astype(str), df["渗透率_pct"], color=C_BLUE, marker="o", linewidth=2)
    for x_, y_ in zip(df["年份"].astype(str), df["渗透率_pct"]):
        ax2.annotate(f"{y_:.1f}%", (x_, y_), textcoords="offset points", xytext=(0, 10),
                     fontsize=8.5, color=C_BLUE, ha="center")
    ax2.set_ylabel("渗透率（%）", fontsize=9, color=C_BLUE)
    ax2.set_ylim(0, 80)
    ax2.tick_params(axis="y", labelcolor=C_BLUE)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=C_RED, label="实际值"), Patch(color="#F87171", label="预测值"),
                       plt.Line2D([0], [0], color=C_BLUE, marker="o", label="渗透率（右轴）")],
              loc="upper left", fontsize=8.5, frameon=False)
    footer(fig,
           "数据来源：网经社电子商务研究中心《2025年度中国私域电商市场数据报告》（2026年5月发布，电数宝数据库）。\n"
           "口径说明：统计对象为「AI私域电商」（私域电商中由AI驱动的部分），非全量中国AI电商GMV。"
           "渗透率=AI私域电商规模/私域电商总规模。深红柱为2025年实际值，浅红柱为2026—2030年预测值。\n"
           "编制：AI电商行业研究报告｜数据截至2026-07")
    fig.savefig(OUT / "05_china_ai_private_ecommerce.png")
    plt.close(fig)


def chart_06_holiday():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.3), gridspec_kw={"width_ratios": [1.3, 1]})
    pairs = [("2025假日季\n(11.1–12.31)", 12900, 2620), ("Cyber Week\n(11.25–12.1)", 3366, 670)]
    x = range(len(pairs))
    w = 0.34
    b1 = ax1.bar([i - w / 2 for i in x], [p[1] for p in pairs], width=w, color=C_GRAY, label="全球线上销售总额")
    b2 = ax1.bar([i + w / 2 for i in x], [p[2] for p in pairs], width=w, color=C_BLUE, label="其中AI与Agent影响")
    ax1.bar_label(b1, fmt="{:,.0f}", fontsize=9)
    ax1.bar_label(b2, fmt="{:,.0f}", fontsize=9)
    for i, p in enumerate(pairs):
        ax1.annotate(f"占{p[2]/p[1]*100:.0f}%订单", (i + w / 2, p[2]),
                     textcoords="offset points", xytext=(0, 16), ha="center", fontsize=9,
                     color=C_BLUE, fontweight="bold")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels([p[0] for p in pairs], fontsize=9.5)
    ax1.set_ylabel("销售额（亿美元）", fontsize=9)
    ax1.set_title("假日季：AI影响的销售规模", fontsize=10.5, loc="left")
    ax1.legend(fontsize=8.5, frameon=False)
    ax1.grid(axis="y", linestyle=":", alpha=0.5)

    growth_labels = ["部署自有Agent\n的零售商", "未部署\n自有Agent"]
    growth_vals = [6.2, 3.9]
    b3 = ax2.bar(growth_labels, growth_vals, color=[C_GREEN, C_GRAY], width=0.45)
    ax2.bar_label(b3, fmt="%.1f%%", fontsize=10.5)
    ax2.set_ylabel("假日季销售同比增速（%）", fontsize=9)
    ax2.set_ylim(0, 8)
    ax2.set_title("自有品牌Agent与销售增速", fontsize=10.5, loc="left")
    ax2.grid(axis="y", linestyle=":", alpha=0.5)
    fig.suptitle("图6  2025假日季AI对零售销售的影响（Salesforce口径）", fontsize=12, x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(rect=[0, 0.04, 1, 0.91])
    footer(fig,
           "数据来源：Salesforce《2025假日购物报告》及Cyber Week报告（基于超过15亿消费者购物数据）。\n"
           "口径说明：「AI与Agent影响的销售」指AI参与推荐、客服或决策过程的订单销售额，不等于在AI对话界面内完成结账的交易。"
           "增速对比口径为假日季销售同比增速。另：假日季Agent自主执行动作同比+142%。\n"
           "编制：AI电商行业研究报告｜数据截至2026-07")
    fig.savefig(OUT / "06_holiday_ai_influence.png")
    plt.close(fig)


def chart_07_scorecard():
    df = pd.read_csv(DATA / "instore_ai_scorecard.csv")
    inside = df[df["证据线"] == "站内导购"].sort_values("数值_pct")
    referral = df[df["证据线"] == "AI引荐流量"].sort_values("数值_pct")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.5), gridspec_kw={"width_ratios": [1.2, 1]})

    def draw(ax, sub, xmax):
        colors = [C_GREEN if c == "效果提升" else C_BLUE for c in sub["类别"]]
        bars = ax.barh(sub["指标"], sub["数值_pct"], color=colors, height=0.55)
        for bar, r in zip(bars, sub.itertuples()):
            ax.text(bar.get_width() + xmax * 0.02, bar.get_y() + bar.get_height() / 2,
                    f"+{r.数值_pct:g}%", va="center", fontsize=9)
        ax.set_xlim(0, xmax)
        ax.grid(axis="x", linestyle=":", alpha=0.5)
        ax.tick_params(axis="y", labelsize=8.5)

    draw(ax1, inside, 250)
    ax1.set_title("路径B：站内AI导购效果", fontsize=10.5, loc="left")
    ax1.set_xlabel("提升幅度 / 同比增速（%）", fontsize=9)
    draw(ax2, referral, 70)
    ax2.set_title("路径A相关：站外AI引荐到站质量", fontsize=10.5, loc="left")
    ax2.set_xlabel("相对非AI渠道的优势（%）", fontsize=9)
    from matplotlib.patches import Patch
    ax1.legend(handles=[Patch(color=C_GREEN, label="效果指标"), Patch(color=C_BLUE, label="使用规模增长")],
               fontsize=8.5, frameon=False, loc="lower right")
    fig.suptitle("图7  站内AI导购与站外AI引荐：分口径效果对照", fontsize=12, x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(rect=[0, 0.06, 1, 0.90])
    footer(fig,
           "数据来源：亚马逊2025Q3/Q4财报电话会；Salesforce 2025假日季报告；Adobe Digital Insights（2026-03）；Shopify（2026-05）。\n"
           "口径说明：左图为站内AI导购工具自身效果（用户完成率、MAU/交互增速、部署Agent的零售商增速溢价）；"
           "右图为站外AI平台引荐流量到零售网站后的转化/RPV优势。两条证据线口径不同，不可合并为单一区间。\n"
           "编制：AI电商行业研究报告｜数据截至2026-07")
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
