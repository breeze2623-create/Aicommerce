#!/usr/bin/env python3
"""AI电商行业研究报告 — 图表生成脚本。

图表编号与报告正文一致：
  图1  全球AI引荐流量：历史增速与累计指数情景外推
  图2  AI引荐流量质量：转化率与单次访问收入
  图3  2025假日季AI对零售销售的影响
  图4  代理式商务规模预测对比
  图5  中国AI私域电商市场规模与渗透率
  图6  主要AI购物入口用户规模对照
  图7  站内AI导购运营指标对照（内部口径）
  图8  站内AI导购有效商品浏览量情景测算
  图9  站内AI导购与站外AI引荐：分口径效果对照
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
from matplotlib.patches import Patch

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
C_PALE = "#CBD5E1"

COMPILER = "编制：AI电商行业研究报告｜数据截至2026-07"
INTERNAL_NOTE = (
    "数据来源：淘宝AI导购与千问电商场景指标为业务方提供的内部运营口径数据（未公开披露，无第三方交叉验证），"
    "仅在本报告内部对照使用，不与QuestMobile等第三方监测口径混排比较。"
)

BASE = {
    "淘宝AI导购": {"dau": 500.0, "ipv": 0.11, "turns": 1.3, "d1": 10.0, "d7": 30.0},
    "千问电商场景": {"dau": 43.0, "ipv": 1.00, "turns": 2.8, "d1": 12.0, "d7": 33.0},
}


def footer(fig, text):
    fig.text(0.01, -0.03, text, fontsize=7.2, color=C_GRAY, ha="left", va="top", wrap=True)


def load_engagement():
    df = pd.read_csv(DATA / "instore_assistant_engagement.csv")
    return df.pivot(index="产品", columns="指标", values="数值")


def compute_scenarios():
    """按假设表逐期复利推演，返回长表：产品/情景/时点/DAU/人均IPV/日均有效商品浏览量。"""
    asm = pd.read_csv(DATA / "instore_scenario_assumptions.csv")
    rows = []
    for product, base in BASE.items():
        for scen in ["保守", "中性", "乐观"]:
            dau, ipv = base["dau"], base["ipv"]
            rows.append([product, scen, "2026年中", dau, ipv, dau * ipv, "实际基期"])
            for period, year in [("2026→2027", "2027年中"), ("2027→2028", "2028年中")]:
                a = asm[(asm.产品 == product) & (asm.情景 == scen) & (asm.期间 == period)].iloc[0]
                dau *= a["DAU年增长倍数"]
                ipv *= a["人均IPV年增长倍数"]
                rows.append([product, scen, year, dau, ipv, dau * ipv, "情景测算"])
    out = pd.DataFrame(rows, columns=["产品", "情景", "时点", "DAU_万人", "人均IPV", "日均有效商品浏览量_万次", "性质"])
    out.round(3).to_csv(DATA / "_computed_scenarios.csv", index=False, encoding="utf-8")
    return out


def compute_traffic_index():
    """AI引荐流量累计指数：以2025Q1=100，按增速年衰减系数外推。"""
    df = pd.read_csv(DATA / "ai_referral_traffic.csv")
    g26 = df[(df.panel == "period") & (df["标签"] == "2026Q1")]["同比增速_pct"].iloc[0] / 100
    params = df[df.panel == "scenario_param"]
    series = {}
    for r in params.itertuples():
        k = r.同比增速_pct / 100
        idx26 = 100 * (1 + g26)
        g27 = g26 * k
        idx27 = idx26 * (1 + g27)
        g28 = g27 * k
        idx28 = idx27 * (1 + g28)
        series[r.标签] = {
            "k": k,
            "index": [100.0, idx26, idx27, idx28],
            "growth": [None, g26, g27, g28],
        }
    return series


# ---------------------------------------------------------------- 图1
def fig01_referral_traffic():
    df = pd.read_csv(DATA / "ai_referral_traffic.csv")
    per = df[(df.panel == "period")]
    series = compute_traffic_index()
    years = ["2025Q1", "2026Q1", "2027Q1", "2028Q1"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.6, 4.4), gridspec_kw={"width_ratios": [1, 1.15]})

    b1 = ax1.bar(per["标签"], per["同比增速_pct"], color=[C_LIGHT, C_PALE, C_BLUE, C_LIGHT], width=0.62)
    ax1.bar_label(b1, fmt="+%g%%", fontsize=9.5, padding=2)
    ax1.set_title("① 已实现：AI引荐流量同比增速（实际值）", fontsize=10.5, loc="left")
    ax1.set_ylabel("同比增速（%）", fontsize=9)
    ax1.tick_params(axis="x", labelsize=8.2, rotation=14)
    ax1.set_ylim(0, 1350)
    ax1.grid(axis="y", linestyle=":", alpha=0.5)

    styles = {"保守": (C_GRAY, ":"), "中性": (C_BLUE, "-"), "乐观": (C_AMBER, "--")}
    for name, s in series.items():
        color, ls = styles[name]
        ax2.plot(years, s["index"], marker="o", markersize=5, linewidth=2, color=color, linestyle=ls,
                 label=f"{name}（增速年衰减系数{s['k']:.0%}）")
        ax2.annotate(f"{s['index'][-1]:,.0f}", (years[-1], s["index"][-1]),
                     textcoords="offset points", xytext=(6, 0), fontsize=9, color=color, va="center")
    ax2.annotate(f"{series['中性']['index'][1]:,.0f}\n（实际）", (years[1], series["中性"]["index"][1]),
                 textcoords="offset points", xytext=(-6, 14), fontsize=8.5, color=C_RED, ha="center")
    ax2.axvspan(1.0, 3.35, color="#F1F5F9", zorder=0)
    ax2.text(2.15, 3200, "情景测算区间", fontsize=8.5, color=C_GRAY, ha="center")
    ax2.set_xlim(-0.25, 3.35)
    ax2.set_ylabel("累计流量指数（2025Q1=100）", fontsize=9)
    ax2.set_ylim(0, 3700)
    ax2.set_title("② 情景外推：AI引荐流量累计指数（2025Q1=100）", fontsize=10.5, loc="left")
    ax2.legend(fontsize=8.2, frameon=False, loc="upper left")
    ax2.grid(axis="y", linestyle=":", alpha=0.5)

    fig.suptitle("图1  全球AI引荐流量：已实现增速与累计指数情景外推",
                 fontsize=12, x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(rect=[0, 0.04, 1, 0.91])
    footer(fig,
           "数据来源：左图为Adobe Digital Insights《季度AI流量报告》（2026年4月发布）实际值；右图2026Q1为同一来源实际值，2027—2028Q1为本报告测算。\n"
           "口径说明：AI引荐流量指从ChatGPT、Gemini、Perplexity等生成式AI平台跳转至零售网站的访问，基于Adobe Analytics覆盖的美国零售网站超1万亿次访问。"
           "累计指数以2025Q1=100，按各期同比增速复利累乘。\n"
           "测算假设：2027Q1与2028Q1同比增速=上一年同比增速×衰减系数（保守30%／中性40%／乐观55%），衰减系数取自2025年12月+1151%至2026年3月+269%的已观测收敛速度。"
           "该外推为本报告测算，非Adobe预测。\n" + COMPILER)
    fig.savefig(OUT / "fig01_ai_referral_traffic_trend.png")
    plt.close(fig)


# ---------------------------------------------------------------- 图2
def fig02_traffic_quality():
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
    ax1.set_title("AI引荐流量质量一年内完成逆转", fontsize=10.5, loc="left")
    ax1.legend(fontsize=8.5, frameon=False, loc="lower right")
    ax1.grid(axis="y", linestyle=":", alpha=0.5)

    b3 = ax2.bar(eng["指标"], eng["数值_pct"], color=C_GREEN, width=0.5)
    ax2.bar_label(b3, fmt="+%g%%", fontsize=10, padding=2)
    ax2.set_title("2026年3月：AI来源访客参与度", fontsize=10.5, loc="left")
    ax2.set_ylabel("相对非AI来源（%）", fontsize=9)
    ax2.set_ylim(0, 60)
    ax2.grid(axis="y", linestyle=":", alpha=0.5)
    fig.suptitle("图2  AI引荐流量质量：转化率与单次访问收入", fontsize=12, x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(rect=[0, 0.04, 1, 0.92])
    footer(fig,
           "数据来源：Adobe Digital Insights（2026年4月发布），基于Adobe Analytics覆盖的美国零售网站访问数据。\n"
           "口径说明：转化率=访问中完成购买的比例；RPV=单次访问收入；正值表示AI来源优于非AI来源。"
           "2025年3月RPV原文表述为「非AI比AI高128%」，换算为AI相对非AI约-56%。参与度为同期AI来源访客相对非AI来源的差异。\n"
           "口径提示：该对比为渠道观察性对比，未控制访客构成差异，不等同于AI渠道的因果效应。\n" + COMPILER)
    fig.savefig(OUT / "fig02_ai_traffic_quality.png")
    plt.close(fig)


# ---------------------------------------------------------------- 图3
def fig03_holiday():
    df = pd.read_csv(DATA / "salesforce_holiday.csv")
    sales = df[df.panel == "sales"]
    v = dict(zip(sales["标签"], sales["数值"]))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.3), gridspec_kw={"width_ratios": [1.3, 1]})
    pairs = [("2025假日季\n(11.1–12.31)", v["2025假日季全球线上销售"], v["其中AI与Agent影响"]),
             ("Cyber Week\n(11.25–12.1)", v["CyberWeek全球销售"], v["其中AI与Agent驱动"])]
    x = range(len(pairs))
    w = 0.34
    b1 = ax1.bar([i - w / 2 for i in x], [p[1] for p in pairs], width=w, color=C_GRAY, label="全球线上销售总额")
    b2 = ax1.bar([i + w / 2 for i in x], [p[2] for p in pairs], width=w, color=C_BLUE, label="其中AI与Agent影响")
    ax1.bar_label(b1, fmt="{:,.0f}", fontsize=9)
    ax1.bar_label(b2, fmt="{:,.0f}", fontsize=9)
    for i, p in enumerate(pairs):
        ax1.annotate(f"占{p[2] / p[1] * 100:.0f}%订单", (i + w / 2, p[2]),
                     textcoords="offset points", xytext=(0, 16), ha="center", fontsize=9,
                     color=C_BLUE, fontweight="bold")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels([p[0] for p in pairs], fontsize=9.5)
    ax1.set_ylabel("销售额（亿美元）", fontsize=9)
    ax1.set_title("假日季：AI影响的销售规模", fontsize=10.5, loc="left")
    ax1.legend(fontsize=8.5, frameon=False)
    ax1.grid(axis="y", linestyle=":", alpha=0.5)

    b3 = ax2.bar(["部署自有Agent\n的零售商", "未部署\n自有Agent"], [6.2, 3.9], color=[C_GREEN, C_GRAY], width=0.45)
    ax2.bar_label(b3, fmt="%.1f%%", fontsize=10.5)
    ax2.set_ylabel("假日季销售同比增速（%）", fontsize=9)
    ax2.set_ylim(0, 8)
    ax2.set_title("自有品牌Agent与销售增速", fontsize=10.5, loc="left")
    ax2.grid(axis="y", linestyle=":", alpha=0.5)
    fig.suptitle("图3  2025假日季AI对零售销售的影响", fontsize=12, x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(rect=[0, 0.04, 1, 0.91])
    footer(fig,
           "数据来源：Salesforce《2025假日购物报告》及Cyber Week报告，基于超过15亿消费者的购物数据。\n"
           "口径说明：「AI与Agent影响的销售」指AI参与推荐、客服或决策过程的订单销售额，属宽口径，不等于在AI对话界面内完成结账的交易（后者约低一个数量级，参见图4）。\n"
           "口径提示：右图为部署与未部署Agent两组零售商的销售增速对比，属观察性分组，未控制企业规模与品类结构差异。另：假日季Agent自主执行动作同比+142%。\n" + COMPILER)
    fig.savefig(OUT / "fig03_holiday_ai_influence.png")
    plt.close(fig)


# ---------------------------------------------------------------- 图4
def fig04_forecasts():
    df = pd.read_csv(DATA / "global_market_forecasts.csv")
    df["mid"] = (df["低值_十亿美元"] + df["高值_十亿美元"]) / 2
    df = df.sort_values("mid")
    labels = [f"{r.机构}｜{r.范围} {r.目标年份}" for r in df.itertuples()]
    fig, ax = plt.subplots(figsize=(9.4, 4.9))
    colors = [C_BLUE if r.范围 == "美国" else C_AMBER for r in df.itertuples()]
    for i, r in enumerate(df.itertuples()):
        lo, hi = r.低值_十亿美元, r.高值_十亿美元
        if lo == hi:
            ax.barh(i, lo, height=0.55, color=colors[i], alpha=0.9)
            ax.text(hi * 1.08, i, f"${hi:,.0f}B", va="center", fontsize=9)
        else:
            ax.barh(i, hi - lo, left=lo, height=0.55, color=colors[i], alpha=0.9)
            ax.text(hi * 1.08, i, f"${lo:,.0f}~{hi:,.0f}B", va="center", fontsize=9)
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(labels, fontsize=9.5)
    ax.set_xscale("log")
    ax.set_xlim(10, 15000)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda val, _: f"{val:,.0f}"))
    ax.set_xlabel("预测规模（十亿美元，对数轴）", fontsize=9)
    ax.set_title("图4  代理式商务规模预测对比：口径差异决定结论差异", fontsize=12, loc="left", fontweight="bold")
    ax.legend(handles=[Patch(color=C_BLUE, label="美国口径"), Patch(color=C_AMBER, label="全球口径")],
              loc="lower right", fontsize=9, frameon=False)
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    footer(fig,
           "数据来源：eMarketer、Morgan Stanley、Bain、McKinsey、Edgar Dunn 公开预测（2025年10月—12月发布）。\n"
           "口径说明：eMarketer仅统计在AI平台内完成结账的交易（窄口径）；Morgan Stanley为代理自主执行的购买；Bain含代理发起／影响／完成的购买；"
           "McKinsey为代理编排的零售收入（含AI影响决策，宽口径）；Edgar Dunn为零售交易流。\n"
           "读图提示：横轴为对数轴。窄口径与宽口径相差约一个数量级以上，且目标年份与地域不同，各条不可直接相加或取均值。\n" + COMPILER)
    fig.savefig(OUT / "fig04_agentic_market_forecasts.png")
    plt.close(fig)


# ---------------------------------------------------------------- 图5
def fig05_china_private():
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
    ax.legend(handles=[Patch(color=C_RED, label="实际值"), Patch(color="#F87171", label="机构预测值"),
                       plt.Line2D([0], [0], color=C_BLUE, marker="o", label="渗透率（右轴）")],
              loc="upper left", fontsize=8.5, frameon=False)
    footer(fig,
           "数据来源：网经社电子商务研究中心《2025年度中国私域电商市场数据报告》（2026年5月发布，电数宝数据库）。\n"
           "口径说明：统计对象为「AI私域电商」，即私域电商中由AI驱动的部分，非全量中国AI电商GMV；"
           "渗透率=AI私域电商规模÷私域电商总规模。深红柱为2025年实际值，浅红柱为该机构2026—2030年预测值（非本报告测算）。\n"
           "读图提示：该口径不可与图4的代理式商务预测直接比较，二者统计对象与地域均不同。\n" + COMPILER)
    fig.savefig(OUT / "fig05_china_ai_private_ecommerce.png")
    plt.close(fig)


# ---------------------------------------------------------------- 图6
def fig06_entrance_scale():
    df = pd.read_csv(DATA / "assistant_scale.csv").sort_values("规模_亿")
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    colors = [C_RED if r == "国内" else C_BLUE for r in df["区域"]]
    bars = ax.barh(df["产品"], df["规模_亿"], color=colors, height=0.55, alpha=0.92)
    for bar, r in zip(bars, df.itertuples()):
        ax.text(bar.get_width() + 0.08, bar.get_y() + bar.get_height() / 2,
                f"{r.规模_亿:g}亿｜{r.口径}｜{r.时点}", va="center", fontsize=8.5)
    ax.set_xlim(0, 12.5)
    ax.set_xlabel("用户规模（亿）", fontsize=9)
    ax.set_title("图6  主要AI购物相关入口用户规模对照", fontsize=12, loc="left", fontweight="bold")
    ax.legend(handles=[Patch(color=C_RED, label="国内"), Patch(color=C_BLUE, label="海外")],
              loc="lower right", fontsize=9, frameon=False)
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    footer(fig,
           "数据来源：QuestMobile（豆包、千问，2026年6月）；OpenAI公开披露（ChatGPT周活跃用户）；Google公开披露（Gemini月活跃用户）；"
           "亚马逊2025Q4财报电话会（Rufus年度累计使用用户）；Perplexity公司公开披露。\n"
           "口径说明：WAU=周活跃用户，MAU=月活跃用户，Rufus为年度累计使用用户。三种口径的统计窗口不同（周／月／年），"
           "数值不可直接横向比较，本图仅用于量级对照。\n"
           "收录规则：仅收录可追溯至第三方监测或公司财报／官方公告的数据；未达置信度门槛的自报运营数据不予展示（见附录B）。\n" + COMPILER)
    fig.savefig(OUT / "fig06_ai_entrance_scale.png")
    plt.close(fig)


# ---------------------------------------------------------------- 图7
def fig07_engagement():
    eng = load_engagement()
    products = ["淘宝AI导购", "千问电商场景"]
    colors = [C_RED, C_BLUE]
    derived_ipv_per_turn = [eng.loc[p, "人均IPV"] / eng.loc[p, "人均对话轮次"] for p in products]
    derived_views = [eng.loc[p, "DAU"] * eng.loc[p, "人均IPV"] for p in products]

    panels = [
        ("使用规模：DAU", [eng.loc[p, "DAU"] for p in products], "万人", "{:.0f}"),
        ("决策深度：人均IPV", [eng.loc[p, "人均IPV"] for p in products], "次/人·日", "{:.2f}"),
        ("会话深度：人均对话轮次", [eng.loc[p, "人均对话轮次"] for p in products], "轮/会话", "{:.1f}"),
        ("次日留存率", [eng.loc[p, "次日留存率"] for p in products], "%", "{:.0f}%"),
        ("7日回访率", [eng.loc[p, "7日回访率"] for p in products], "%", "{:.0f}%"),
        ("派生：日均有效商品浏览量", derived_views, "万次/日", "{:.0f}"),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(11.8, 6.1))
    for ax, (title, vals, unit, fmt) in zip(axes.flat, panels):
        bars = ax.bar(["淘宝\nAI导购", "千问\n电商场景"], vals, color=colors, width=0.5, alpha=0.92)
        ax.bar_label(bars, labels=[fmt.format(v) for v in vals], fontsize=10.5, padding=3, fontweight="bold")
        ax.set_title(title, fontsize=10, loc="left")
        ax.set_ylabel(unit, fontsize=8.5)
        ax.set_ylim(0, max(vals) * 1.55)
        ax.tick_params(axis="x", labelsize=9)
        ax.grid(axis="y", linestyle=":", alpha=0.45)
        ratio = vals[1] / vals[0] if vals[0] else 0
        ax.text(0.97, 0.94, f"千问÷淘宝 = {ratio:.2f}×", transform=ax.transAxes,
                fontsize=8.8, color=C_GRAY, ha="right", va="top")

    fig.suptitle("图7  站内AI导购运营指标对照：规模大不等于价值大（内部口径）",
                 fontsize=12, x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(rect=[0, 0.03, 1, 0.93])
    footer(fig,
           INTERNAL_NOTE + "\n"
           "口径说明：DAU=使用该AI导购功能／触发电商场景的去重日活跃用户；人均IPV=每使用用户日均产生的商品详情页浏览次数；"
           "人均对话轮次=单次会话内平均对话轮数；次日留存率=D+1回访占比。\n"
           "「7日回访率」口径校正：原始表述为「7日留存30%／33%」，但单日留存随时间单调不增、不可能高于次日留存，"
           f"故判定其口径为7日窗口内至少回访一次，报告按此解读，且不与次日留存做同类比较。\n"
           f"派生指标算法：日均有效商品浏览量＝DAU×人均IPV（淘宝 500万×0.11＝{derived_views[0]:.0f}万次／日；"
           f"千问 43万×1.00＝{derived_views[1]:.0f}万次／日）；每轮对话产出＝人均IPV÷人均对话轮次"
           f"（淘宝{derived_ipv_per_turn[0]:.3f}／千问{derived_ipv_per_turn[1]:.3f}次，假设二者同为人均口径，属近似量级）。\n"
           "可比性提示：两侧入口曝光机制不同（淘宝为高流量电商App内的入口曝光，千问为用户主动触发的通用助手场景），"
           "DAU统计的意图强度不一致；且淘宝站内用户可绕过AI链路直达商品，归因规则可能低估其IPV。\n" + COMPILER)
    fig.savefig(OUT / "fig07_instore_assistant_engagement.png")
    plt.close(fig)


# ---------------------------------------------------------------- 图8
def fig08_scenario():
    sc = compute_scenarios()
    points = ["2026年中", "2027年中", "2028年中"]
    scen_style = {"保守": C_PALE, "中性": C_BLUE, "乐观": C_AMBER}

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.6))
    for ax, product in zip(axes, ["淘宝AI导购", "千问电商场景"]):
        sub = sc[sc.产品 == product]
        base = sub[sub.时点 == "2026年中"]["日均有效商品浏览量_万次"].iloc[0]
        w = 0.24
        ax.bar([0], [base], width=0.34, color=C_GRAY, label="实际基期")
        ax.annotate(f"{base:.0f}", (0, base), textcoords="offset points", xytext=(0, 4),
                    ha="center", fontsize=9.5, fontweight="bold")
        for si, (scen, color) in enumerate(scen_style.items()):
            vals = [sub[(sub.情景 == scen) & (sub.时点 == t)]["日均有效商品浏览量_万次"].iloc[0] for t in points[1:]]
            xs = [1 + (si - 1) * w, 2 + (si - 1) * w]
            ax.bar(xs, vals, width=w, color=color, label=scen)
            for x_, v_ in zip(xs, vals):
                ax.annotate(f"{v_:.0f}", (x_, v_), textcoords="offset points", xytext=(0, 3),
                            ha="center", fontsize=8.5)
        ax.set_xticks([0, 1, 2])
        ax.set_xticklabels(points, fontsize=9.5)
        ax.set_ylabel("日均有效商品浏览量（万次／日）", fontsize=8.5)
        ax.set_title(product, fontsize=11, loc="left", fontweight="bold")
        ax.grid(axis="y", linestyle=":", alpha=0.45)
        ax.legend(fontsize=8.5, frameon=False, ncol=2, loc="upper left")
        ax.set_ylim(0, max(sub["日均有效商品浏览量_万次"]) * 1.32)

    fig.suptitle("图8  站内AI导购有效商品浏览量情景测算（非预测）",
                 fontsize=12, x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(rect=[0, 0.05, 1, 0.92])
    footer(fig,
           "数据来源：2026年中基期为业务方提供的内部运营口径数据（见图7）；2027—2028年为本报告按公开锚点设定假设后的测算，非任何机构预测。\n"
           "测算方法：日均有效商品浏览量＝DAU×人均IPV，两项分别按情景假设的年增长倍数逐期复利推演（假设明细见 data/instore_scenario_assumptions.csv）。\n"
           "关键假设与锚点：①增速衰减参照Adobe口径AI引荐流量由+1151%收敛至+269%的已观测速度；"
           "②高增长档参照亚马逊披露的Rufus月活同比+149%、交互量同比+210%；"
           "③淘宝侧人均IPV的上限锚定于千问电商场景当前实测值1.00次／人·日，乐观档2028年仅取0.59次，未突破该锚点。\n"
           "使用限制：本测算仅推演流量与浏览深度，未推演成交额；由浏览量到GMV需引入详情页转化率与客单价两项敞口参数，"
           "本报告不做单点估计，避免用假设堆叠出规模结论。\n" + COMPILER)
    fig.savefig(OUT / "fig08_instore_scenario_projection.png")
    plt.close(fig)


# ---------------------------------------------------------------- 图9
def fig09_scorecard():
    df = pd.read_csv(DATA / "effect_scorecard.csv")
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
    ax1.set_title("站内自有AI导购效果", fontsize=10.5, loc="left")
    ax1.set_xlabel("提升幅度 / 同比增速（%）", fontsize=9)
    draw(ax2, referral, 70)
    ax2.set_title("站外AI引荐到站质量", fontsize=10.5, loc="left")
    ax2.set_xlabel("相对非AI渠道的优势（%）", fontsize=9)
    ax1.legend(handles=[Patch(color=C_GREEN, label="效果指标"), Patch(color=C_BLUE, label="使用规模增长")],
               fontsize=8.5, frameon=False, loc="lower right")
    fig.suptitle("图9  站内AI导购与站外AI引荐：分口径效果对照", fontsize=12, x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(rect=[0, 0.06, 1, 0.90])
    footer(fig,
           "数据来源：亚马逊2025Q3／Q4财报电话会（公司口径）；Salesforce《2025假日购物报告》；Adobe Digital Insights（2026年3月）；Shopify公开数据（2026年5月）。\n"
           "口径说明：左图为站内AI导购工具自身效果（使用者购买完成率、月活与交互同比增速、部署自有Agent零售商的增速溢价）；"
           "右图为站外AI平台引荐流量到达零售网站后的转化率与单次访问收入优势。两条证据线口径不同，不可合并为单一区间。\n"
           "因果性提示：「Rufus使用者购买完成率+60%」为使用者与未使用者的观察性对比，主动使用AI工具的用户本身购买意向更强，"
           "存在自选择偏差；在缺少对照实验或倾向得分匹配的情况下，该数值应视为相关性上限而非因果效应。\n" + COMPILER)
    fig.savefig(OUT / "fig09_effect_scorecard.png")
    plt.close(fig)


if __name__ == "__main__":
    for stale in OUT.glob("*.png"):
        stale.unlink()
    fig01_referral_traffic()
    fig02_traffic_quality()
    fig03_holiday()
    fig04_forecasts()
    fig05_china_private()
    fig06_entrance_scale()
    fig07_engagement()
    fig08_scenario()
    fig09_scorecard()
    print("已生成图表：")
    for path in sorted(OUT.glob("*.png")):
        print(" -", path.relative_to(ROOT))
    print("\n情景测算结果：")
    print(pd.read_csv(DATA / "_computed_scenarios.csv").to_string(index=False))
    print("\nAI引荐流量累计指数：")
    for name, s in compute_traffic_index().items():
        idx = ", ".join(f"{v:,.0f}" for v in s["index"])
        gro = ", ".join("—" if g is None else f"+{g:.0%}" for g in s["growth"])
        print(f" {name}（k={s['k']:.0%}）指数[2025Q1,2026Q1,2027Q1,2028Q1] = {idx}｜同比 = {gro}")
