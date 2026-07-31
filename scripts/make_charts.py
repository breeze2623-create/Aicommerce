#!/usr/bin/env python3
"""AI电商行业研究报告 — 图表生成脚本。

图表编号与报告正文一致：
  图1  美国零售网站AI引荐流量：已实现增速与定基指数情景外推
  图2  AI引荐流量质量：转化率与单次访问收入
  图3  2025假日季AI对零售销售的影响
  图4  代理式商务规模预测对比
  图5  中国AI私域电商市场规模与渗透率
  图6  主要AI购物入口用户规模对照
  图7  站内AI导购运营指标对照（内部口径）
  图8  站内AI导购有效商品浏览量情景测算
  图9  站内AI导购与站外AI引荐：分口径效果对照
  图10 AI导购 vs 传统电商导购：进商详效率对照
  图11 同口径对照：淘宝／千问／Rufus（Rufus七项均未取得）
"""

import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
from decimal import ROUND_HALF_UP, Decimal
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# 报告版（charts/）内嵌标题与四段式脚注，供文档独立阅读；
# 演示版（charts/slide/）去掉内嵌标题与脚注，由PPT的页面标题与页级注承载，避免双标题与放映尺度下不可读的微字。
SLIDE_MODE = "--slides" in sys.argv
OUT = ROOT / ("charts/slide" if SLIDE_MODE else "charts")
OUT.mkdir(parents=True, exist_ok=True)

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
INK_TEXT = "#1F2937"

COMPILER = "编制：AI电商行业研究报告｜数据截至2026-07"
INTERNAL_NOTE = (
    "数据来源：淘宝AI导购与千问电商场景指标为业务方提供的内部运营口径数据（未公开披露，无第三方交叉验证），"
    "仅在本报告内部对照使用，不与QuestMobile等第三方监测口径混排比较。"
)

BASE = {
    "淘宝AI导购": {"dau": 500.0, "ipv": 0.11, "turns": 1.3, "d1": 10.0, "d7": 30.0},
    "千问电商场景": {"dau": 43.0, "ipv": 1.00, "turns": 2.8, "d1": 12.0, "d7": 33.0},
}


FOOTER_FS = 7.2


def suptitle(fig, text, **kw):
    if not SLIDE_MODE:
        fig.suptitle(text, **kw)


def maintitle(ax, text, **kw):
    if not SLIDE_MODE:
        ax.set_title(text, **kw)


def r0(x):
    """四舍五入到整数（ROUND_HALF_UP）。Python 默认的 round-half-even 会让 64.5→64、747.5→748，
    导致图表标签与正文取整结果不一致，故统一走此函数。"""
    return int(Decimal(repr(float(x))).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def r2(x):
    return float(Decimal(repr(float(x))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _visual_len(text):
    """CJK字符按1个字宽计，其余按0.55个字宽计。"""
    return sum(1.0 if ord(c) > 0x2E7F else 0.55 for c in text)


def _tokens(para):
    """把段落切成不可再拆的单元：单个CJK字符，或一段连续的拉丁/数字词。"""
    buf = ""
    for ch in para:
        if ord(ch) > 0x2E7F or ch.isspace():
            if buf:
                yield buf
                buf = ""
            yield ch
        else:
            buf += ch
    if buf:
        yield buf


def _wrap(text, budget):
    """按可视宽度换行，不拆断拉丁词。matplotlib 的 wrap=True 与 bbox_inches='tight' 同用会撑宽画布，故手动换行。"""
    out = []
    for para in text.split("\n"):
        line, used = "", 0.0
        for tok in _tokens(para):
            w = _visual_len(tok)
            if used + w > budget and line:
                out.append(line.rstrip())
                line, used = "", 0.0
                if tok.isspace():
                    continue
            line += tok
            used += w
        out.append(line.rstrip())
    # 避免标点或极短片段孤立成行（如换行后只剩一个句号）
    merged = []
    for ln in out:
        if merged and _visual_len(ln) <= 2 and all(not (c.isalnum() or ord(c) > 0x2E7F) or c in "。，；：、）」" for c in ln):
            merged[-1] += ln
        else:
            merged.append(ln)
    return "\n".join(merged)


def footer(fig, text):
    if SLIDE_MODE:
        return
    # matplotlib 不渲染 markdown，星号会原样出现在图注中，统一转为书名号
    text = re.sub(r"\*\*(.+?)\*\*", r"「\1」", text)
    if "*" in text:
        raise SystemExit(f"图注含未处理的星号：{text[:80]}")
    budget = fig.get_size_inches()[0] * 72 / FOOTER_FS * 0.99
    fig.text(0.01, -0.03, _wrap(text, budget), fontsize=FOOTER_FS, color=C_GRAY,
             ha="left", va="top", linespacing=1.5)


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
                # 先收敛浮点误差再进入下一期，避免 650×1.15=747.4999… 被取整为747
                dau = round(dau * a["DAU年增长倍数"], 6)
                ipv = round(ipv * a["人均IPV年增长倍数"], 6)
                rows.append([product, scen, year, dau, ipv, dau * ipv, "情景测算"])
    out = pd.DataFrame(rows, columns=["产品", "情景", "时点", "DAU_万人", "人均IPV", "日均有效商品浏览量_万次", "性质"])
    # 展示列：图表标签与报告正文一律引用这三列，确保取整结果一致
    out["DAU_展示"] = out["DAU_万人"].map(r0)
    out["人均IPV_展示"] = out["人均IPV"].map(r2)
    out["浏览量_展示"] = out["日均有效商品浏览量_万次"].map(r0)
    out.round(4).to_csv(DATA / "_computed_scenarios.csv", index=False, encoding="utf-8")
    return out


def compute_traffic_index():
    """AI引荐流量定基水平指数：以2025Q1=100，按增速年保留系数外推。"""
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

    b1 = ax1.bar(per["标签"], per["同比增速_pct"], color=[C_PALE, C_PALE, C_BLUE, C_LIGHT], width=0.62)
    ax1.bar_label(b1, fmt="+%g%%", fontsize=9.5, padding=2)
    ax1.legend(handles=[Patch(color=C_PALE, label="2025年窗口（假日季含12月）"),
                        Patch(color=C_BLUE, label="2026Q1（外推基点）"),
                        Patch(color=C_LIGHT, label="2026年3月（含于2026Q1）")],
               fontsize=7.6, frameon=False, loc="upper right")
    ax1.set_title("① 已实现：AI引荐流量同比增速（四个窗口互有嵌套，非独立时点序列）",
                  fontsize=9.6, loc="left")
    ax1.set_ylabel("同比增速（%）", fontsize=9)
    ax1.tick_params(axis="x", labelsize=8.2, rotation=14)
    ax1.set_ylim(0, 1560)
    ax1.grid(axis="y", linestyle=":", alpha=0.5)

    styles = {"保守": (C_GRAY, ":"), "中性": (C_BLUE, "-"), "乐观": (C_AMBER, "--")}
    for name, s in series.items():
        color, ls = styles[name]
        ax2.plot(years, s["index"], marker="o", markersize=5, linewidth=2, color=color, linestyle=ls,
                 label=f"{name}（增速年保留系数{s['k']:.0%}）")
        ax2.annotate(f"{s['index'][-1]:,.0f}", (years[-1], s["index"][-1]),
                     textcoords="offset points", xytext=(6, 0), fontsize=9, color=color, va="center")
    ax2.annotate(f"{series['中性']['index'][1]:,.0f}\n（实际）", (years[1], series["中性"]["index"][1]),
                 textcoords="offset points", xytext=(-6, 14), fontsize=8.5, color=C_RED, ha="center")
    ax2.axvspan(1.0, 3.35, color="#F1F5F9", zorder=0)
    ax2.text(2.15, 3200, "情景测算区间", fontsize=8.5, color=C_GRAY, ha="center")
    ax2.set_xlim(-0.25, 3.35)
    ax2.set_ylabel("指数值", fontsize=9)
    ax2.set_ylim(0, 3700)
    ax2.set_title("② 情景外推：AI引荐流量定基水平指数（2025Q1=100，非累计总量）", fontsize=10.5, loc="left")
    ax2.legend(fontsize=8.2, frameon=False, loc="upper left")
    ax2.grid(axis="y", linestyle=":", alpha=0.5)

    suptitle(fig, "图1  美国零售网站AI引荐流量：已实现增速与定基指数情景外推",
                 fontsize=12, x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(rect=[0, 0.04, 1, 0.91])
    footer(fig,
           "数据来源：左图为Adobe Digital Insights《季度AI流量报告》（2026年4月发布）实际值；右图2026Q1为同一来源实际值，2027—2028Q1为本报告测算。\n"
           "口径说明：AI引荐流量指从ChatGPT、Gemini、Perplexity等生成式AI平台跳转至零售网站的访问，基于Adobe Analytics覆盖的美国零售网站超1万亿次访问；不含中国市场。"
           "定基指数以2025Q1=100，按各期同比增速复利累乘得到各期的流量水平，不是流量累计总量。\n"
           "测算假设：2027Q1与2028Q1同比增速＝上一年同比增速×年保留系数（保守30%／中性40%／乐观55%）。系数为设定值而非推导值：已观测的两个收敛比分别为"
           "269%÷1151%＝0.23（3个月）与269%÷393%＝0.68，二者差异主要来自2025年12月为假日季峰值，含季节性成分，直接年化（0.23⁴≈0.003）会得到近乎归零的结果，"
           "与渠道仍在扩张的事实矛盾。故本报告不由单期观测外推，改为给出一个覆盖面较宽的系数区间，读者可自行替换参数复算。\n"
           "读图提示：左面板的四个窗口互有嵌套——「2025假日季」包含「2025年12月」，「2026Q1」包含「2026年3月」，"
           "因此不构成一条独立的时点序列，不可按柱高顺序读作单调下降的趋势线；右面板才是按季度对齐的可比序列。\n"
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
    ax1.set_ylabel("相对非AI渠道（%）", fontsize=9)
    ax1.set_title("质量指标一年内完成反转", fontsize=10.5, loc="left")
    ax1.legend(fontsize=8.5, frameon=False, loc="lower right")
    ax1.grid(axis="y", linestyle=":", alpha=0.5)

    b3 = ax2.bar(eng["指标"], eng["数值_pct"], color=C_GREEN, width=0.5)
    ax2.bar_label(b3, fmt="+%g%%", fontsize=10, padding=2)
    ax2.set_title("2026年3月：AI来源访客参与度", fontsize=10.5, loc="left")
    ax2.set_ylabel("相对非AI来源（%）", fontsize=9)
    ax2.set_ylim(0, 60)
    ax2.grid(axis="y", linestyle=":", alpha=0.5)
    suptitle(fig, "图2  AI引荐流量的质量指标一年内反转：转化率由−38%转为+42%（渠道观察性对比）",
                 fontsize=11.5, x=0.01, ha="left", fontweight="bold")
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
        ax1.annotate(f"占销售额{p[2] / p[1] * 100:.1f}%", (i + w / 2, p[2]),
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
    suptitle(fig, "图3  假日季AI影响的销售约2620亿美元，但这是「影响」宽口径而非AI界面内成交",
                 fontsize=11.5, x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(rect=[0, 0.04, 1, 0.91])
    footer(fig,
           "数据来源：Salesforce《2025假日购物报告》及Cyber Week报告，基于超过15亿消费者的购物数据。\n"
           "口径说明：「AI与Agent影响的销售」指AI参与推荐、客服或决策过程的订单销售额，属宽口径，不等于在AI对话界面内完成结账的交易（两者地域与周期不同，不可相除取倍数；量级参照见图4）。\n"
           "读图提示：柱高与柱上标注均为「销售额」口径；Salesforce另按「订单」口径给出「AI影响约20%订单」，两个口径数值接近但不等价，不可互换引用。\n"
           "口径提示：右图为部署与未部署自有品牌Agent两组零售商的销售增速对比，属观察性分组，未控制企业规模与品类结构差异；「自有品牌Agent」为企业侧Agent的宽口径，"
           "不等同于站内AI导购工具，故未纳入图9的站内导购证据线。另：假日季Agent自主执行动作同比+142%。\n" + COMPILER)
    fig.savefig(OUT / "fig03_holiday_ai_influence.png")
    plt.close(fig)


# ---------------------------------------------------------------- 图4
def fig04_forecasts():
    df = pd.read_csv(DATA / "global_market_forecasts.csv")
    df["mid"] = (df["低值_十亿美元"] + df["高值_十亿美元"]) / 2
    df = df.sort_values("mid")
    labels = [f"{r.机构}｜{r.范围} {r.目标年份}" for r in df.itertuples()]
    fig, ax = plt.subplots(figsize=(10.0, 4.9))
    width_of = {"仅AI平台内完成结账的交易": ("窄", C_BLUE),
                "代理自主执行的购买": ("中", C_GREEN),
                "代理发起/影响/完成的购买": ("宽", C_AMBER),
                "代理编排的零售收入(含AI影响决策)": ("宽", C_AMBER),
                "代理编排的零售收入(全球)": ("宽", C_AMBER),
                "零售交易流(窄/宽口径)": ("混合", C_GRAY)}
    colors = [width_of[r.口径][1] for r in df.itertuples()]
    for i, r in enumerate(df.itertuples()):
        lo, hi = r.低值_十亿美元, r.高值_十亿美元
        if lo == hi:
            ax.plot([lo], [i], marker="D", markersize=8, color=colors[i])
            ax.text(hi * 1.12, i, f"${hi:,.1f}B（点估计）", va="center", fontsize=9)
        else:
            ax.plot([lo, hi], [i, i], color=colors[i], linewidth=7, alpha=0.9,
                    solid_capstyle="butt")
            ax.plot([lo, hi], [i, i], "|", color=colors[i], markersize=11)
            ax.text(hi * 1.12, i, f"${lo:,.0f}~{hi:,.0f}B（区间）", va="center", fontsize=9)
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(labels, fontsize=9.5)
    ax.set_ylim(-0.7, len(df) - 0.3)
    ax.set_xscale("log")
    ax.set_xlim(10, 20000)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda val, _: f"{val:,.0f}"))
    ax.set_xlabel("预测规模（十亿美元，对数轴）", fontsize=9)
    maintitle(ax, "图4  代理式商务规模预测：口径宽窄造成的差距大于机构之间的差距",
                 fontsize=11.5, loc="left", fontweight="bold")
    ax.legend(handles=[Patch(color=C_BLUE, label="窄口径：仅AI平台内结账"),
                       Patch(color=C_GREEN, label="中口径：代理自主执行的购买"),
                       Patch(color=C_AMBER, label="宽口径：代理编排／影响的零售收入"),
                       Patch(color=C_GRAY, label="混合口径")],
              loc="lower right", fontsize=8.5, frameon=False)
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    footer(fig,
           "数据来源：eMarketer、Morgan Stanley、Bain、McKinsey、Edgar Dunn 公开预测（2025年10月—12月发布）；全部为机构预测值，非实测数据。\n"
           "口径说明：eMarketer仅统计在AI平台内完成结账的交易（窄口径）；Morgan Stanley为代理自主执行的购买；Bain含代理发起／影响／完成的购买；"
           "McKinsey为代理编排的零售收入（含AI影响决策，宽口径）；Edgar Dunn为零售交易流。\n"
           "读图提示：横轴为对数轴。「颜色编码口径宽窄」（地域与年份已写在纵轴标签内）；菱形标记为机构点估计，线段为机构给出的区间，两者不可混读。"
           "读法（倍数须按可比配对给出）：同地域同年份（美国2030年）表中无窄口径数据点，可比的是中口径下限1900亿至宽口径上限10000亿，相差约5.3倍；窄口径对宽口径需跨年份——eMarketer美国2029年1440亿对McKinsey美国2030年9000至10000亿，相差约6.3至6.9倍。本图不使用「相差一个数量级」这一表述。口径宽窄造成的差距大于同口径内不同机构之间的差距，这是本图要说明的主要事实。"
           "各条目标年份与地域不同，不可直接相加或取均值。\n" + COMPILER)
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
    maintitle(ax, "图5  中国AI私域电商：渗透率预测升至约3.8倍，而隐含的私域底盘五年只增约36%",
                 fontsize=11.2, loc="left", fontweight="bold")
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
           "首要口径保留：该机构未公开「AI驱动」的操作化定义（何种参与程度计入），属宽口径，与本报告批评的「AI影响」类口径同类问题。"
           "因此本图只能用于观察趋势方向，不宜作为规模基数或折算依据。\n"
           "口径说明：统计对象为「AI私域电商」，即私域电商中由AI驱动的部分，非全量中国AI电商GMV；"
           "渗透率＝AI私域电商规模÷私域电商总规模。深红柱为2025年实际值，浅红柱为该机构2026—2030年预测值（非本报告测算）。"
           "原始来源以两位小数给出16.79%（2025实测）与64.07%（2030预测），属虚假精度，本图与报告一律按一位小数呈现。\n"
           "自洽性反算（本报告计算）：以规模÷渗透率反推隐含的私域电商总盘＝2025年0.65÷16.8%≈3.87万亿元、2030年3.37÷64.1%≈5.26万亿元，"
           "五年复合增速约6.3%（底盘五年只增约36%）；而渗透率升至约3.8倍。且3.87万亿元仅为同机构口径中国电商总规模59.2万亿元的约6.5%。"
           "该组合在逻辑上并非不可能（AI替代私域内的非AI部分），但读者应据此自行判断其可信度。\n"
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
                f"{r.展示标签}｜{r.口径}｜{r.时点}", va="center", fontsize=8.5)
    ax.set_xlim(0, 13.5)
    ax.set_xlabel("用户规模（亿）", fontsize=9)
    maintitle(ax, "图6  中国与海外主要AI购物入口用户规模对照（统计窗口不同，仅作量级参照）",
                 fontsize=12, loc="left", fontweight="bold")
    ax.legend(handles=[Patch(color=C_RED, label="国内"), Patch(color=C_BLUE, label="海外")],
              loc="lower right", fontsize=9, frameon=False)
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    footer(fig,
           "数据来源：QuestMobile（豆包、千问，2026年6月）；OpenAI公开披露（ChatGPT周活跃用户）；Google公开披露（Gemini月活跃用户）；"
           "亚马逊2025Q4财报电话会（Rufus年度累计使用用户）；Perplexity公司公开披露。\n"
           "口径说明：WAU=周活跃用户，MAU=月活跃用户，Rufus为年度累计使用用户。三种统计窗口（周／月／年）不同，条形长度不构成可比排名，"
           "本图仅用于量级参照——尤其Rufus的年度累计用户天然大于同等活跃度产品的月活，不可据此判断其活跃规模高于Perplexity等。\n"
           "区间处理：Perplexity公司披露为0.3～0.45亿区间，柱长取上界0.45亿作图，标签保留原始区间，正文一律引用区间不取单点。\n"
           "收录规则：仅收录可追溯至第三方监测或公司财报／官方公告的数据；未达置信度门槛的自报运营数据不予展示（见附录B）。\n" + COMPILER)
    fig.savefig(OUT / "fig06_ai_entrance_scale.png")
    plt.close(fig)


# ---------------------------------------------------------------- 图7
def fig07_engagement():
    eng = load_engagement()
    products = ["淘宝AI导购", "千问电商场景"]
    colors = [C_RED, C_BLUE]
    per_turn = [eng.loc[p_, "人均IPV"] / eng.loc[p_, "人均对话轮次"] for p_ in products]
    views = [eng.loc[p_, "DAU"] * eng.loc[p_, "人均IPV"] for p_ in products]

    panels = [
        ("使用规模：DAU", [eng.loc[p_, "DAU"] for p_ in products], "万人", "{:.0f}", False),
        ("决策深度：人均IPV", [eng.loc[p_, "人均IPV"] for p_ in products], "次/人·日", "{:.2f}", False),
        ("会话深度：人均对话轮次", [eng.loc[p_, "人均对话轮次"] for p_ in products], "轮/会话", "{:.1f}", False),
        ("派生：每轮对话产出的商品浏览", per_turn, "次/轮", "{:.3f}", True),
        ("次日留存率", [eng.loc[p_, "次日留存率"] for p_ in products], "%", "{:.0f}%", False),
        ("7日回访率", [eng.loc[p_, "7日回访率"] for p_ in products], "%", "{:.0f}%", False),
        ("派生：日均有效商品浏览量", views, "万次/日", "{:.0f}", True),
    ]

    fig, axes = plt.subplots(2, 4, figsize=(13.2, 6.2))
    flat = axes.flat
    for ax, (title, vals, unit, fmt, derived) in zip(flat, panels):
        bars = ax.bar(["淘宝\nAI导购", "千问\n电商场景"], vals, color=colors, width=0.5,
                      alpha=0.92, hatch="//" if derived else None, edgecolor="white" if derived else None)
        ax.bar_label(bars, labels=[fmt.format(v) for v in vals], fontsize=10, padding=3, fontweight="bold")
        ax.set_title(title, fontsize=9.6, loc="left", color=C_GRAY if derived else "black")
        ax.set_ylabel(unit, fontsize=8.5)
        ax.set_ylim(0, max(vals) * 1.55)
        ax.tick_params(axis="x", labelsize=8.8)
        ax.grid(axis="y", linestyle=":", alpha=0.45)
        ratio = vals[1] / vals[0] if vals[0] else 0
        # 人均IPV 的锚点为整数1.00，精度不足以支撑两位小数，故按「约9倍量级」呈现
        label = "千问÷淘宝 ≈ 9倍量级" if title.startswith("决策深度") else f"千问÷淘宝 ≈ {ratio:.2f}×"
        ax.text(0.97, 0.94, label, transform=ax.transAxes,
                fontsize=8.4, color=C_GRAY, ha="right", va="top")
    last = list(axes.flat)[-1]
    last.axis("off")
    last.text(0.0, 0.92,
              "本图的判读顺序\n\n"
              "① DAU 与人均IPV 的两组倍数方向相反、量级相近，\n"
              "   几近相互抵消，乘积为 0.78×——因此\n"
              "   「DAU为11.63倍、浏览量仅为1.28倍」与\n"
              "   「人均IPV约差9倍」是同一事实的两种表述。\n\n"
              "② 真正提供额外信息的是「每轮对话产出」：\n"
              "   差距落在交互层（0.085 对 0.357 次／轮），\n"
              "   而非用户层。斜纹柱为本报告派生指标。\n\n"
              "③ 留存两项仅约1.1～1.2×，说明差距不在\n"
              "   「是否愿意再来」，而在「来了是否进入选品」。",
              fontsize=8.2, color=INK_TEXT, va="top", linespacing=1.5)

    suptitle(fig, "图7  差距落在交互层：每轮对话产出0.085次对0.357次（≈4.22×，成立边界 u×s＜3.5）｜内部口径 P3",
                 fontsize=12, x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(rect=[0, 0.03, 1, 0.93])
    footer(fig,
           INTERNAL_NOTE + "\n"
           "口径说明：DAU=使用该AI导购功能／触发电商场景的去重日活跃用户；人均IPV=每使用用户日均产生的商品详情页浏览次数；"
           "人均对话轮次=单次会话内平均对话轮数；次日留存率=D+1回访占比。\n"
           "「7日回访率」口径校正：原始表述为「7日留存30%／33%」，但单日留存随时间单调不增、不可能高于次日留存，"
           "故判定其口径为7日窗口内至少回访一次，报告按此解读，且不与次日留存做同类比较。\n"
           f"派生指标算法（斜纹柱）：日均有效商品浏览量＝DAU×人均IPV（淘宝 500万×0.11＝{views[0]:.0f}万次／日；"
           f"千问 43万×1.00＝{views[1]:.0f}万次／日）；每轮对话产出＝人均IPV÷人均对话轮次"
           f"（淘宝{per_turn[0]:.3f}／千问{per_turn[1]:.3f}次）。后者假设两项同为人均口径，属近似量级。\n"
           "精度提示：千问人均IPV为整数1.00（淘宝侧为两位有效数字0.11），无法判断是舍入值还是定义性产物（如「每会话至少浏览1件」），"
           "故全文的深度倍数一律表述为「约9倍量级」，本图标注亦加约等号。\n"
           "可比性提示：①两侧入口曝光机制不同（淘宝为高流量电商App内的入口曝光，千问为用户主动触发的通用助手场景），DAU统计的意图强度不一致；"
           "②淘宝站内用户可绕过AI链路直达商品，归因规则可能低估其IPV，低估倍数记为u（压力区间2～3）；"
           "③IPV为日度口径、轮次为会话内均值，「每轮产出」只在「每人每日约1个会话」时才严格成立，两侧人均日会话数之比记为s（上限2）。\n"
           "「联合敏感度与反转边界（不可省略）」：②③以乘积形式进入，交互层差距＝4.22÷(u×s)。u×s＝2时为2.11倍、＝3时为1.41倍，仍高于留存层差距（1.10～1.20倍）；"
           "达到约3.5及以上时降至留存层以下、方向反转。同一乘积还决定改造路径排序且阈值更低（≈1.96与≈2.75）。三道阈值构成同一量上的嵌套判据，完整表见报告§1.6与§1.8分析五。\n" + COMPILER)
    fig.savefig(OUT / "fig07_instore_assistant_engagement.png")
    plt.close(fig)


# ---------------------------------------------------------------- 图8
def fig08_scenario():
    sc = compute_scenarios()
    points = ["2026年中", "2027年中", "2028年中"]
    scen_style = {"保守": C_PALE, "中性": C_BLUE, "乐观": C_AMBER}
    ymax = sc["日均有效商品浏览量_万次"].max() * 1.42

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.0))
    for ax, product in zip(axes, ["淘宝AI导购", "千问电商场景"]):
        sub = sc[sc.产品 == product]
        base = sub[sub.时点 == "2026年中"].iloc[0]
        w = 0.24
        ax.bar([0], [base["日均有效商品浏览量_万次"]], width=0.34, color=C_GRAY, label="实际基期")
        ax.annotate(f"{base['浏览量_展示']:.0f}\nDAU {base['DAU_展示']:.0f}万\nIPV {base['人均IPV_展示']:.2f}",
                    (0, base["日均有效商品浏览量_万次"]), textcoords="offset points", xytext=(0, 4),
                    ha="center", fontsize=7.8, color=C_GRAY)
        for si, (scen, color) in enumerate(scen_style.items()):
            rows = [sub[(sub.情景 == scen) & (sub.时点 == t)].iloc[0] for t in points[1:]]
            xs = [1 + (si - 1) * w, 2 + (si - 1) * w]
            ax.bar(xs, [r["日均有效商品浏览量_万次"] for r in rows], width=w, color=color, label=scen)
            for x_, r in zip(xs, rows):
                ax.annotate(f"{r['浏览量_展示']:.0f}\n{r['DAU_展示']:.0f}万\n{r['人均IPV_展示']:.2f}",
                            (x_, r["日均有效商品浏览量_万次"]), textcoords="offset points", xytext=(0, 3),
                            ha="center", fontsize=7.2, color="#374151")
        ax.set_xticks([0, 1, 2])
        ax.set_xticklabels(points, fontsize=9.5)
        ax.set_title(product, fontsize=11, loc="left", fontweight="bold")
        ax.grid(axis="y", linestyle=":", alpha=0.45)
        ax.legend(fontsize=8.5, frameon=False, ncol=2, loc="upper left")
        lo = sub[sub.时点 == "2026年中"]["日均有效商品浏览量_万次"].iloc[0]
        hi = sub["日均有效商品浏览量_万次"].max()
        # 两面板各用自身量程以保证面板内可读；纵轴上限统一按「基期的20倍」缩放，
        # 使两面板的柱高在视觉上表达相同的「相对基期的倍数」，从而仍可跨面板比较。
        ax.set_ylim(0, lo * 20)
        ax.set_ylabel("日均有效商品浏览量（万次／日）", fontsize=9)
        ax.text(0.02, 0.79, f"纵轴上限＝本侧基期×20；柱高表达相对基期的倍数，可跨面板比较",
                transform=ax.transAxes, fontsize=7.8, color=C_GRAY, ha="left", va="top")
        ax.text(0.02, 0.725, f"本面板内部跨度：{lo:.0f} → {hi:.0f}万次／日（相对基期{hi / lo:.1f}倍）",
                transform=ax.transAxes, fontsize=8.2, color=C_GRAY, ha="left", va="top")

    suptitle(fig, "图8  情景测算：两侧驱动结构不同——淘宝靠深度与规模双轮，千问几乎全靠规模（非预测）",
                 fontsize=11.5, x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(rect=[0, 0.05, 1, 0.92])
    footer(fig,
           "数据来源：2026年中基期为业务方提供的内部运营口径数据（见图7）；2027—2028年为本报告按公开锚点设定假设后的测算，非任何机构预测。\n"
           "读图提示：两面板各用自身量程，但**纵轴上限统一设为本侧基期的20倍**，因此柱高表达的是「相对基期的倍数」，可跨面板比较；"
           "绝对值请读柱上数字。2026年中两侧基期接近（55对43万次／日），到2028年中乐观档拉开约2.8倍。"
           "柱上三行依次为有效商品浏览量、DAU、人均IPV，便于核对乘积来源；图表与报告正文共用同一取整规则（ROUND_HALF_UP）。\n"
           "测算方法：日均有效商品浏览量＝DAU×人均IPV，两项分别按情景假设的年增长倍数逐期复利推演"
           "（假设明细见 data/instore_scenario_assumptions.csv，含展示取整列的中间结果见 data/_computed_scenarios.csv）。\n"
           "关键假设与锚点：①增速收敛参照Adobe口径AI引荐流量的已观测放缓趋势（系数为设定值，推导限制见图1图注）；"
           "②高增长档参照亚马逊披露的Rufus月活同比+149%、交互量同比+210%（公司口径）——需说明两点弱点：该两项分别为用户数与交互次数口径，"
           "此处仅借其量级设定用户数增速，属跨口径借用；且淘宝侧乐观档实取×2.00、千问侧实取×3.00，两侧取值不同是因两侧基数与渗透空间不同，属编制方判断；"
           "③深度上限分两侧设定——淘宝侧以千问当前实测1.00次／人·日为追赶上限，乐观档2028年中仅达0.59次；千问侧因已处同类已实证最高水平，"
           "设定两年累计深度提升不超过20%（乐观档约1.20次）。两侧上限性质不同，不可混用。\n"
           "使用限制：本测算仅推演流量与浏览深度，未推演成交额；由浏览量到GMV需引入详情页转化率与客单价两项敞口参数，"
           "本报告不做单点估计，避免用假设堆叠出规模结论。另需注意：本图的区间宽度（淘宝侧约5.9倍）全部来自DAU与人均IPV两个流量层假设，"
           "并不包含转化率与客单价的敞口，因此它衡量的是「流量层自身」的不确定性。\n" + COMPILER)
    fig.savefig(OUT / "fig08_instore_scenario_projection.png")
    plt.close(fig)


# ---------------------------------------------------------------- 图9
def fig09_scorecard():
    """按「对照构造」分面板：同一面板内的对照组构造与量纲一致，避免跨构造的无效排名。"""
    df = pd.read_csv(DATA / "effect_scorecard.csv")
    groups = [
        ("① 使用者 对 未使用者\n（站内自有导购）", "使用者对未使用者", 90, "相对未使用者的提升（%）"),
        ("② AI渠道 对 非AI渠道\n（站外AI引荐）", "AI渠道对非AI渠道", 90, "相对非AI渠道的优势（%）：\n转化率或单次访问收入，见标签"),
        ("③ 同比增速\n（规模增长，两条证据线并列）", "同比增速", 470, "同比增速（%）：\n访问／交互／用户，见标签"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(13.0, 4.3), gridspec_kw={"width_ratios": [0.72, 1.15, 1.25]})
    for ax, (title, key, xmax, xlabel) in zip(axes, groups):
        sub = df[df["对照构造"] == key].sort_values("数值_pct")
        colors = [C_GREEN if line == "站内自有导购" else C_BLUE for line in sub["证据线"]]
        bars = ax.barh(sub["指标"], sub["数值_pct"], color=colors, height=0.5)
        for bar, r in zip(bars, sub.itertuples()):
            ax.text(bar.get_width() + xmax * 0.02, bar.get_y() + bar.get_height() / 2,
                    f"+{r.数值_pct:g}%", va="center", fontsize=9)
        ax.set_xlim(0, xmax)
        ax.set_title(title, fontsize=9.6, loc="left")
        ax.set_xlabel(xlabel, fontsize=8.6)
        ax.grid(axis="x", linestyle=":", alpha=0.5)
        ax.tick_params(axis="y", labelsize=8.2)
    suptitle(fig, "图9  站内AI导购的公开效果证据只有一个数据点（面板①）",
                 fontsize=12, x=0.01, ha="left", fontweight="bold")
    fig.legend(handles=[Patch(color=C_GREEN, label="站内自有导购"), Patch(color=C_BLUE, label="站外AI引荐")],
               fontsize=8.5, frameon=False, ncol=2, loc="upper right", bbox_to_anchor=(0.995, 0.995))
    fig.tight_layout(rect=[0, 0.06, 1, 0.895])
    footer(fig,
           "数据来源：亚马逊2025Q4财报电话会（Rufus三项，公司口径）；Adobe Digital Insights（2026年3月转化与RPV、2026Q1流量增速）；Shopify公开披露（2026年5月）。\n"
           "分面板规则：「按对照组构造分面板」，同一面板内的对照组与量纲一致，避免跨构造的无效排名。面板①为「使用者对未使用者」（个体层对比），"
           "面板②为「AI渠道对非AI渠道」（渠道层对比），面板③为同比增速。颜色区分证据线（站内自有导购／站外AI引荐）。三个面板之间不可合并为单一区间。\n"
           "面板②内含两类指标：转化率优势（Adobe +42%、Shopify +54%）与单次访问收入优势（Adobe RPV +37%），二者对照组构造相同但被测量的量不同，已在标签中写明。\n"
           "本图的主要事实：面板①只有一根柱——站内AI导购在全球范围内仅有Amazon Rufus一个公开的效果数据点，且为观察性对比。"
           "这既说明该方向的公开证据基础很薄，也说明自建随机对照实验是当前最可靠、且可自主取得的识别途径（分阶段放量支持的准实验识别可作退路，但需额外的平行趋势假设）。\n"
           "因果性提示：面板①与②的全部数值均为观察性对比。「Rufus使用者购买完成率+60%」中主动使用AI工具的用户购买意向本就更强，存在自选择偏差；"
           "Adobe与Shopify的渠道对比未控制访客构成差异，且同期AI渠道流量大幅扩张（Q1对Q1定基指数100→493即4.93倍，3月对3月约3.7倍），访客构成必然发生迁移。均应视为相关性上限而非因果效应。\n"
           "同构造差异说明：Adobe（+42%）与Shopify（+54%）测量同一构造但相差12个百分点，来自面板差异——Adobe覆盖美国大型零售网站，"
           "Shopify以中小与DTC商家为主，且Shopify未披露完整方法。两者应作为区间理解（约+42%～+54%），不取单点。\n"
           "未纳入说明：Salesforce「部署自有品牌Agent的零售商增速6.2%对未部署3.9%」为企业层分组对比（第三种对照构造），"
           "且「自有品牌Agent」口径宽于站内AI导购，故不纳入本图，仅在报告§1.2的假日季数据表与图3中列示。\n" + COMPILER)
    fig.savefig(OUT / "fig09_effect_scorecard.png")
    plt.close(fig)


# ---------------------------------------------------------------- 图10
def fig10_ai_vs_traditional():
    """AI导购 vs 传统电商导购：只画有公开可追溯或内部实测支撑的指标；空值不画柱。"""
    import math

    # 进商详到达率：传统＝有点击率下界；AI两侧＝1−e^(−人均IPV)
    reach = {
        "传统搜索\n（淘宝）": 90.0,
        "淘宝\nAI导购": (1 - math.exp(-0.11)) * 100,
        "千问\n电商场景": (1 - math.exp(-1.00)) * 100,
    }
    reach_colors = [C_GREEN, C_RED, C_BLUE]
    reach_notes = [">=90%\n（有点击率下界）", f"≈{reach['淘宝\nAI导购']:.1f}%\n（日度派生）", f"≈{reach['千问\n电商场景']:.1f}%\n（日度派生）"]

    # 规模：App DAU vs 功能 DAU（搜索功能DAU未取得，用App作天花板）
    scale_labels = ["淘宝App\nDAU", "淘宝\nAI导购", "千问\n电商场景"]
    scale_vals = [40200.0, 500.0, 43.0]
    scale_colors = [C_GREEN, C_RED, C_BLUE]
    scale_fmts = ["4.02亿", "500万", "43万"]
    ai_share = 500.0 / 40200.0 * 100  # ≈1.24%

    # 转化率锚点：App层有值，AI链路空
    conv_labels = ["淘宝App", "行业均值", "AI导购链路"]
    conv_vals = [8.2, 4.5, None]
    conv_colors = [C_GREEN, C_GRAY, C_PALE]

    # 每交互商品产出：传统空，AI有派生
    yield_labels = ["传统搜索\n每次搜索IPV", "淘宝AI\n每轮产出", "千问\n每轮产出"]
    yield_vals = [None, 0.085, 0.357]
    yield_colors = [C_PALE, C_RED, C_BLUE]

    # Hybrid相对提升（传统搜推被大模型增强）
    hybrid_labels = ["复杂词\n相关性", "推荐信息流\n点击率"]
    hybrid_vals = [20.0, 10.0]
    hybrid_units = ["+20 PT", "+10%"]

    fig, axes = plt.subplots(2, 3, figsize=(13.2, 6.4))

    # --- 面板1：进商详到达率（核心）
    ax = axes[0, 0]
    bars = ax.bar(list(reach.keys()), list(reach.values()), color=reach_colors, width=0.55, alpha=0.92)
    ax.bar_label(bars, labels=reach_notes, fontsize=8.2, padding=2, fontweight="bold")
    ax.set_title("① 进商详到达率（核心对照）", fontsize=9.8, loc="left", fontweight="bold")
    ax.set_ylabel("%", fontsize=8.5)
    ax.set_ylim(0, 118)
    ax.axhline(90, color=C_GREEN, linestyle="--", linewidth=0.8, alpha=0.5)
    ax.grid(axis="y", linestyle=":", alpha=0.45)
    ax.tick_params(axis="x", labelsize=8.2)
    ax.text(0.97, 0.06, "构造不同：左＝单次搜索有点击；\n右二＝日度至少1次商详（派生）",
            transform=ax.transAxes, fontsize=7.2, color=C_GRAY, ha="right", va="bottom")

    # --- 面板2：规模
    ax = axes[0, 1]
    bars = ax.bar(scale_labels, scale_vals, color=scale_colors, width=0.55, alpha=0.92)
    ax.bar_label(bars, labels=scale_fmts, fontsize=9, padding=2, fontweight="bold")
    ax.set_yscale("log")
    ax.set_title("② 使用规模（对数轴）", fontsize=9.8, loc="left", fontweight="bold")
    ax.set_ylabel("万人（对数）", fontsize=8.5)
    ax.set_ylim(20, 120000)
    ax.grid(axis="y", linestyle=":", alpha=0.45)
    ax.tick_params(axis="x", labelsize=8.2)
    ax.text(0.97, 0.94, f"淘宝AI ≈ App DAU的 {ai_share:.1f}%",
            transform=ax.transAxes, fontsize=8.0, color=C_GRAY, ha="right", va="top")
    ax.text(0.97, 0.06, "搜索功能DAU未公开；\nApp DAU仅为天花板参照",
            transform=ax.transAxes, fontsize=7.2, color=C_GRAY, ha="right", va="bottom")

    # --- 面板3：转化率锚点
    ax = axes[0, 2]
    plot_vals = [v if v is not None else 0 for v in conv_vals]
    bars = ax.bar(conv_labels, plot_vals, color=conv_colors, width=0.55, alpha=0.92)
    labels = ["8.2%", "4.5%", "未取得"]
    for b, lab, v in zip(bars, labels, conv_vals):
        if v is None:
            ax.text(b.get_x() + b.get_width() / 2, 1.2, "未取得\n（P4不展示）",
                    ha="center", va="bottom", fontsize=8.2, color=C_GRAY, fontweight="bold")
            b.set_hatch("//")
            b.set_edgecolor("white")
            b.set_height(0.15)
        else:
            ax.text(b.get_x() + b.get_width() / 2, v + 0.25, lab,
                    ha="center", va="bottom", fontsize=9.5, fontweight="bold")
    ax.set_title("③ 转化率锚点（App层 ≠ AI链路）", fontsize=9.8, loc="left", fontweight="bold")
    ax.set_ylabel("%", fontsize=8.5)
    ax.set_ylim(0, 12)
    ax.grid(axis="y", linestyle=":", alpha=0.45)
    ax.tick_params(axis="x", labelsize=8.2)
    ax.text(0.97, 0.94, "淘宝意图明确用户转化\n显著高于行业均值",
            transform=ax.transAxes, fontsize=7.4, color=C_GRAY, ha="right", va="top")

    # --- 面板4：每交互产出
    ax = axes[1, 0]
    plot_vals = [v if v is not None else 0 for v in yield_vals]
    bars = ax.bar(yield_labels, plot_vals, color=yield_colors, width=0.55, alpha=0.92)
    for b, v in zip(bars, yield_vals):
        if v is None:
            ax.text(b.get_x() + b.get_width() / 2, 0.02, "未取得\n平台级绝对值",
                    ha="center", va="bottom", fontsize=8.0, color=C_GRAY, fontweight="bold")
            b.set_hatch("//")
            b.set_edgecolor("white")
            b.set_height(0.012)
        else:
            ax.text(b.get_x() + b.get_width() / 2, v + 0.012, f"{v:.3f}",
                    ha="center", va="bottom", fontsize=9.5, fontweight="bold")
    ax.set_title("④ 每交互商品产出（交互层）", fontsize=9.8, loc="left", fontweight="bold")
    ax.set_ylabel("次／交互", fontsize=8.5)
    ax.set_ylim(0, 0.48)
    ax.grid(axis="y", linestyle=":", alpha=0.45)
    ax.tick_params(axis="x", labelsize=7.8)
    ax.text(0.97, 0.94, "商家侧IPV/UV=1.5~3属店级经验，\nP4不采纳为平台搜索基线",
            transform=ax.transAxes, fontsize=7.0, color=C_GRAY, ha="right", va="top")

    # --- 面板5：Hybrid相对提升
    ax = axes[1, 1]
    bars = ax.bar(hybrid_labels, hybrid_vals, color=[C_AMBER, C_AMBER], width=0.5, alpha=0.92)
    ax.bar_label(bars, labels=hybrid_units, fontsize=10, padding=3, fontweight="bold")
    ax.set_title("⑤ 传统搜推被大模型增强（相对提升）", fontsize=9.8, loc="left", fontweight="bold")
    ax.set_ylabel("相对提升", fontsize=8.5)
    ax.set_ylim(0, 28)
    ax.grid(axis="y", linestyle=":", alpha=0.45)
    ax.tick_params(axis="x", labelsize=8.2)
    ax.text(0.97, 0.94, "AB测试（阿里官方披露）\n说明：是相对提升，非绝对CTR",
            transform=ax.transAxes, fontsize=7.2, color=C_GRAY, ha="right", va="top")

    # --- 面板6：读法
    ax = axes[1, 2]
    ax.axis("off")
    ax.text(0.0, 0.96,
            "本图的判读顺序\n\n"
            "① 进商详效率：传统搜索有点击率≥90%，\n"
            "   淘宝AI日度商详发生率仅≈10%——\n"
            "   即使构造不完全相同，量级差距约一个\n"
            "   数量级；千问≈63%，仍低于传统搜索。\n\n"
            "② 规模：淘宝AI DAU仅为App的约1.2%；\n"
            "   传统搜索仍是意图购物的主入口。\n\n"
            "③ 转化：App层8.2%证明「有意图就能转」；\n"
            "   AI链路转化率公开与内部均未取得。\n\n"
            "④⑤ 交互产出与Hybrid：传统搜索的每次\n"
            "   搜索IPV绝对值未公开；已知的是传统\n"
            "   搜推仍在被大模型增强（+20PT／+10%），\n"
            "   AI导购尚不能替代搜索主链路。",
            fontsize=8.0, color=INK_TEXT, va="top", linespacing=1.45)

    suptitle(fig,
             "图10  相对传统搜索，站内AI导购的进商详效率仍差约一个数量级｜公开P1/P2＋内部P3",
             fontsize=11.8, x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(rect=[0, 0.03, 1, 0.93])
    footer(fig,
           "数据来源：①传统搜索有点击率≥90%——36氪（2025-09-17）引述接近手淘消息人士对传统搜索成熟度的表述（P2下界）；"
           "淘宝／千问进商详到达率由内部人均IPV按1−e^(−λ)派生（P3派生）。"
           "②淘宝App DAU 4.02亿——QuestMobile（36氪快讯转引，2025年6月平均日活，P1）。"
           "③淘宝转化率8.2%／行业4.5%——QuestMobile（36氪2025-09引述，P1）；AI链路转化率未取得。"
           "④每轮产出同图7派生；传统每次搜索IPV平台级绝对值未公开。"
           "⑤复杂词相关性+20PT、推荐CTR+10%——阿里搜推智能总裁凯夫，新浪科技双11报道（2025-11-12，P2，AB测试相对提升）。\n"
           "口径说明：本图把「传统电商导购」操作化为淘宝传统搜索（含搜推Hybrid），不含直播带货与人工客服——后两者缺少与AI导购同构造的平台级公开效率数据，"
           "商家侧客服询单转化经验值（约15%～30%）与店级IPV/UV经验区间（1.5～3）属P4，本报告不展示。\n"
           "构造差异（不可省略）：面板①左侧为「单次搜索会话的有点击率」，右侧为「日度至少产生1次商详的发生率」；二者分母与时间窗不同，"
           "只能作量级对照，不能直接相减得出「效率差X个百分点」。面板②的App DAU不是搜索功能DAU。面板③的App转化率不是AI链路转化率。\n"
           "判读边界：本图支持「当前站内AI导购在进商详效率上显著低于成熟传统搜索、且规模仍为App的约1%量级」这一方向性判断；"
           "不支持「AI导购转化优于／劣于搜索」——该判断需AI链路转化率实测后方可作出。\n" + COMPILER)
    fig.savefig(OUT / "fig10_ai_vs_traditional_guide.png")
    plt.close(fig)


# ---------------------------------------------------------------- 图11
def fig11_rufus_same_metric_gap():
    """图7同口径三方对照：淘宝／千问有内部实测；Rufus七项同口径均未取得，空位不填数。"""
    eng = load_engagement()
    align = pd.read_csv(DATA / "rufus_engagement_alignment.csv")
    # 保真闸：对齐表中七项主指标必须全部为「未取得」；若日后有同口径数进入，应改画柱而非静默跳过。
    core_rows = align[~align["指标"].str.startswith("参考_")]
    if not (core_rows["Rufus是否取得"] == "否").all():
        raise SystemExit("fig11 保真闸失败：rufus_engagement_alignment.csv 出现已取得的同口径主指标，须改画柱")
    if not (core_rows["Rufus同口径数值"] == "—").all():
        raise SystemExit("fig11 保真闸失败：Rufus同口径数值列不应填入推算值")

    products = ["淘宝AI导购", "千问电商场景"]
    colors = [C_RED, C_BLUE]
    labels = ["淘宝\nAI导购", "千问\n电商场景", "Amazon\nRufus"]
    per_turn = [eng.loc[p_, "人均IPV"] / eng.loc[p_, "人均对话轮次"] for p_ in products]
    views = [eng.loc[p_, "DAU"] * eng.loc[p_, "人均IPV"] for p_ in products]

    panels = [
        ("使用规模：DAU", [eng.loc[p_, "DAU"] for p_ in products], "万人", "{:.0f}", False),
        ("决策深度：人均IPV", [eng.loc[p_, "人均IPV"] for p_ in products], "次/人·日", "{:.2f}", False),
        ("会话深度：人均对话轮次", [eng.loc[p_, "人均对话轮次"] for p_ in products], "轮/会话", "{:.1f}", False),
        ("派生：每轮对话产出的商品浏览", per_turn, "次/轮", "{:.3f}", True),
        ("次日留存率", [eng.loc[p_, "次日留存率"] for p_ in products], "%", "{:.0f}%", False),
        ("7日回访率", [eng.loc[p_, "7日回访率"] for p_ in products], "%", "{:.0f}%", False),
        ("派生：日均有效商品浏览量", views, "万次/日", "{:.0f}", True),
    ]

    fig, axes = plt.subplots(2, 4, figsize=(13.6, 6.4))
    for ax, (title, vals, unit, fmt, derived) in zip(axes.flat, panels):
        xs = [0, 1, 2]
        bars = ax.bar(xs[:2], vals, color=colors, width=0.55, alpha=0.92,
                      hatch="//" if derived else None, edgecolor="white" if derived else None)
        ax.bar_label(bars, labels=[fmt.format(v) for v in vals], fontsize=9.5, padding=3, fontweight="bold")
        # Rufus：同口径未取得 —— 不画假柱，只标空位
        ax.scatter([2], [0], marker="x", s=70, color=C_GRAY, zorder=3, linewidths=1.6)
        ax.text(2, max(vals) * 0.08, "未取得\n同口径", ha="center", va="bottom",
                fontsize=8.2, color=C_GRAY, linespacing=1.25)
        ax.set_xticks(xs)
        ax.set_xticklabels(labels, fontsize=8.4)
        ax.set_title(title, fontsize=9.4, loc="left", color=C_GRAY if derived else "black")
        ax.set_ylabel(unit, fontsize=8.3)
        ax.set_ylim(0, max(vals) * 1.60)
        ax.grid(axis="y", linestyle=":", alpha=0.45)
        ratio = vals[1] / vals[0] if vals[0] else 0
        label = "千问÷淘宝 ≈ 9倍量级｜Rufus —" if title.startswith("决策深度") else f"千问÷淘宝 ≈ {ratio:.2f}×｜Rufus —"
        ax.text(0.98, 0.94, label, transform=ax.transAxes,
                fontsize=7.6, color=C_GRAY, ha="right", va="top")

    last = list(axes.flat)[-1]
    last.axis("off")
    last.text(
        0.0, 0.96,
        "独立校验结论（保真）\n\n"
        "① 图7的七项指标在Rufus侧均无同口径公开值：\n"
        "   DAU／人均IPV／对话轮次／次日留存／7日回访\n"
        "   及两项派生指标——全部标「未取得」，不推算填数。\n\n"
        "② Rufus实际披露的是另一套口径（不可混入本图）：\n"
        "   年度累计使用用户超3亿（≠DAU）；\n"
        "   月活同比+149%、交互量同比+210%（≠绝对值）；\n"
        "   购买完成率相对未使用者约高60%（效果对照，见图9）；\n"
        "   增量年化销售近120亿美元（归因未完整披露）。\n\n"
        "③ 校验范围：亚马逊2025Q4财报电话会、2026Q2新闻稿、\n"
        "   公司产品说明及交叉二手报道；底表见\n"
        "   data/rufus_engagement_alignment.csv。",
        fontsize=7.9, color=INK_TEXT, va="top", linespacing=1.45,
    )

    suptitle(fig,
             "图11  同口径对照：淘宝／千问有实测，Rufus七项均未取得（空位不填数｜保真校验）",
             fontsize=12, x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(rect=[0, 0.03, 1, 0.93])
    footer(fig,
           "数据来源：淘宝／千问七项同图7（内部运营口径P3）；Rufus侧经独立校验后确认无同口径公开值，故空位标注「未取得」——"
           "对齐底表见 data/rufus_engagement_alignment.csv。\n"
           "口径说明（与图7完全一致，便于逐项对照）：DAU=功能／场景去重日活跃；人均IPV=每使用用户日均经该链路的商品详情页浏览；"
           "人均对话轮次=单次会话内平均轮数；次日留存=D+1回访占比；7日回访率=7日窗口至少回访一次（非第7日单日留存）；"
           "派生：每轮产出＝人均IPV÷人均对话轮次；日均有效商品浏览量＝DAU×人均IPV。\n"
           "不可替代说明：Rufus的「年度累计使用用户」「月活同比」「交互量同比」「购买完成率＋60%」「增量年化销售」分属规模累计、增速、效果对照与成交归因，"
           "与上列运营参与度指标构造不同，禁止折算填入本图空位；已取得者分别落在图6／图8脚注／图9面板①与§2.3.1。\n"
           "保真规则：本图脚本含闸——若对齐表主指标出现「已取得」或非「—」数值而仍画空位，生成时直接报错；禁止用跨口径推算补柱。\n"
           + COMPILER)
    fig.savefig(OUT / "fig11_rufus_same_metric_gap.png")
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
    fig10_ai_vs_traditional()
    fig11_rufus_same_metric_gap()
    print("已生成图表：")
    for path in sorted(OUT.glob("*.png")):
        print(" -", path.relative_to(ROOT))
    print("\n情景测算结果：")
    print(pd.read_csv(DATA / "_computed_scenarios.csv")[["产品","情景","时点","DAU_展示","人均IPV_展示","浏览量_展示"]].to_string(index=False))
    print("\nAI引荐流量定基指数：")
    for name, s in compute_traffic_index().items():
        idx = ", ".join(f"{v:,.0f}" for v in s["index"])
        gro = ", ".join("—" if g is None else f"+{g:.0%}" for g in s["growth"])
        print(f" {name}（k={s['k']:.0%}）指数[2025Q1,2026Q1,2027Q1,2028Q1] = {idx}｜同比 = {gro}")
