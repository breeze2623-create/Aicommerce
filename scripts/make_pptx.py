#!/usr/bin/env python3
"""生成《AI 电商行业研究》沃尔玛中国 CTO 汇报 PPT（16:9）。

用法：python3 scripts/make_pptx.py
输出：report/AI电商行业研究_沃尔玛中国CTO汇报.pptx + report/pptx_outline.md（评审用文字稿）
"""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
CHARTS = ROOT / "charts"
OUT = ROOT / "report"
OUT.mkdir(exist_ok=True)

# 品牌色
BLUE = RGBColor(0x00, 0x71, 0xCE)      # Walmart blue
DARK = RGBColor(0x0B, 0x1F, 0x3A)
INK = RGBColor(0x1F, 0x29, 0x37)
GRAY = RGBColor(0x6B, 0x72, 0x80)
YELLOW = RGBColor(0xFF, 0xC2, 0x20)    # Walmart spark yellow
RED = RGBColor(0xB4, 0x23, 0x18)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT = RGBColor(0xF3, 0xF6, 0xFB)

FONT = "Microsoft YaHei"  # 交付环境常见中文字体；渲染端缺失时自动替换为本机 CJK 字体

SW, SH = Inches(13.333), Inches(7.5)

outline_lines = []


def set_font(run, size=14, bold=False, color=INK, name=FONT):
    f = run.font
    f.size = Pt(size)
    f.bold = bold
    f.color.rgb = color
    f.name = name
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = rPr.makeelement(qn("a:ea"), {})
        rPr.append(ea)
    ea.set("typeface", name)


def add_textbox(slide, x, y, w, h, lines, align=PP_ALIGN.LEFT):
    """lines: list of (text, size, bold, color, bullet_level or None)"""
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    first = True
    for text, size, bold, color, level in lines:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        if level is not None:
            p.level = level
        run = p.add_run()
        run.text = text
        set_font(run, size=size, bold=bold, color=color)
        p.space_after = Pt(max(4, size * 0.35))
    return tb


def add_rect(slide, x, y, w, h, fill, line=None):
    from pptx.enum.shapes import MSO_SHAPE

    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
    sh.shadow.inherit = False
    return sh


def new_slide(prs, title=None, kicker=None, page_no=None, title_color=INK):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    if kicker:
        add_rect(slide, Inches(0.55), Inches(0.42), Inches(0.14), Inches(0.5), YELLOW)
        add_textbox(slide, Inches(0.82), Inches(0.36), Inches(11.6), Inches(0.4),
                    [(kicker, 12, True, BLUE, None)])
    if title:
        add_textbox(slide, Inches(0.8), Inches(0.72), Inches(12.0), Inches(1.0),
                    [(title, 22, True, title_color, None)])
        outline_lines.append(f"\n## 第 {page_no} 页｜{kicker or ''}｜{title}")
    # 页脚
    add_textbox(slide, Inches(0.55), Inches(7.08), Inches(12.2), Inches(0.35),
                [("沃尔玛中国 CTO 汇报｜AI 电商行业研究（预读版 v1.0）｜数据截至 2026-07｜内部资料·注意保密"
                  + (f"｜{page_no}" if page_no else ""), 8.5, False, GRAY, None)])
    return slide


def note(slide, text, y=Inches(6.62)):
    add_textbox(slide, Inches(0.8), y, Inches(11.9), Inches(0.45),
                [(text, 9.5, False, GRAY, None)])
    outline_lines.append(f"    注：{text}")


def bullets(slide, items, x=Inches(0.8), y=Inches(1.7), w=Inches(11.9), h=Inches(4.8), size=15):
    lines = []
    for it in items:
        if isinstance(it, tuple):
            head, body = it
            lines.append((f"◆ {head}", size, True, INK, 0))
            if body:
                lines.append((body, size - 1.5, False, INK, 1))
        else:
            lines.append((f"◆ {it}", size, False, INK, 0))
    add_textbox(slide, x, y, w, h, lines)
    for it in items:
        if isinstance(it, tuple):
            outline_lines.append(f"    - {it[0]}：{it[1]}")
        else:
            outline_lines.append(f"    - {it}")


def image_slide(prs, kicker, title, img, page_no, src_note, img_h=4.7):
    slide = new_slide(prs, title=title, kicker=kicker, page_no=page_no)
    from PIL import Image

    with Image.open(CHARTS / img) as im:
        w_px, h_px = im.size
    disp_h = Inches(img_h)
    disp_w = Emu(int(disp_h * w_px / h_px))
    max_w = Inches(12.2)
    if disp_w > max_w:
        disp_w = max_w
        disp_h = Emu(int(disp_w * h_px / w_px))
    left = Emu(int((SW - disp_w) / 2))
    slide.shapes.add_picture(str(CHARTS / img), left, Inches(1.75), width=disp_w, height=disp_h)
    note(slide, src_note)
    outline_lines.append(f"    [图：charts/{img}]")
    return slide


def table_slide(prs, kicker, title, page_no, headers, rows, col_widths, src_note, font_size=11, row_h=0.52):
    slide = new_slide(prs, title=title, kicker=kicker, page_no=page_no)
    n_rows, n_cols = len(rows) + 1, len(headers)
    x, y = Inches(0.8), Inches(1.75)
    total_w = sum(col_widths)
    tbl_shape = slide.shapes.add_table(n_rows, n_cols, x, y, Inches(total_w), Inches(row_h * n_rows))
    tbl = tbl_shape.table
    for j, wj in enumerate(col_widths):
        tbl.columns[j].width = Inches(wj)
    for j, htxt in enumerate(headers):
        cell = tbl.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = BLUE
        p = cell.text_frame.paragraphs[0]
        run = p.add_run()
        run.text = htxt
        set_font(run, size=font_size, bold=True, color=WHITE)
    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = LIGHT if i % 2 else WHITE
            cell.margin_top = Pt(3)
            cell.margin_bottom = Pt(3)
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            run = p.add_run()
            run.text = str(val)
            low_trust = "低置信" in str(val)
            set_font(run, size=font_size - (1 if len(str(val)) > 60 else 0), bold=False,
                     color=RED if low_trust else INK)
    note(slide, src_note)
    outline_lines.append("    [表] " + " | ".join(headers))
    for row in rows:
        outline_lines.append("      " + " | ".join(str(v) for v in row))
    return slide


def build():
    prs = Presentation()
    prs.slide_width = SW
    prs.slide_height = SH
    pn = 0

    # ---- 1 封面 ----
    pn += 1
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(slide, 0, 0, SW, SH, DARK)
    add_rect(slide, Inches(0.9), Inches(2.02), Inches(0.18), Inches(1.65), YELLOW)
    add_textbox(slide, Inches(1.25), Inches(1.55), Inches(11.3), Inches(2.6), [
        ("AI 电商行业研究", 40, True, WHITE, None),
        ("格局、威胁与沃尔玛中国的行动选项", 24, False, RGBColor(0xBF, 0xDB, 0xFE), None),
    ])
    add_textbox(slide, Inches(1.25), Inches(4.35), Inches(11.0), Inches(2.2), [
        ("汇报对象：沃尔玛中国 CTO", 15, True, WHITE, None),
        ("版本：预读版 v1.0 ｜ 数据截至 2026-07 ｜ 配套预读文档 30 分钟", 12.5, False, RGBColor(0x93, 0xC5, 0xFD), None),
        ("数据纪律：全部数字标注来源与置信度；京东系自报数据按内部研判整体降级为『低置信』，图表以斜纹标注，不作为决策依据", 12.5, False, YELLOW, None),
        ("质量控制：本汇报经独立评审盲评循环（评分标准见附录），达标后提交", 12.5, False, RGBColor(0x93, 0xC5, 0xFD), None),
    ])
    outline_lines.append("## 第 1 页｜封面｜AI 电商行业研究：格局、威胁与沃尔玛中国的行动选项（含数据纪律与质量控制声明）")

    # ---- 2 三个判断 ----
    pn += 1
    slide = new_slide(prs, kicker="执行摘要 1/2", title="三个判断：入口在前移、交易留本地、山姆最受益也最受攻", page_no=pn)
    bullets(slide, [
        ("判断一｜购物决策入口正在前移到对话框，速度快于预期",
         "美国零售 AI 导流 2026Q1 同比 +393%，转化率一年内 -38% → +42%（Adobe，高置信）；假日季 20% 全球零售订单、2620 亿美元受 AI 影响（Salesforce，高置信）；国内豆包 3.83 亿 MAU 已闭环抖音电商、千问通淘宝、元宝通京东。观望窗口以季度计"),
        ("判断二｜交易不会被第三方 AI 拿走，但『决策』会——正确姿势已被沃尔玛美国验证",
         "ChatGPT 站内代结账转化仅为商家自有渠道约 1/3，上线约半年收缩；Sparky 以插件进驻 ChatGPT/Gemini、把交易带回自有体系后，转化恢复到自有站约 70%。中国的舞台是微信/豆包/千问"),
        ("判断三｜山姆是中国最适合 AI 导购的零售资产，也是 AI 比价/平替攻击的头号标靶",
         "约 4000 精选 SKU + 1070 万会员 + 线上占比超 50% + 补货指令自动化近 90% → AI 推荐准确率与 ROI 天花板最高；反面：『山姆平替』内容截流决策，美团小象+叮咚约 2000 前置仓正面进攻即时零售腹地"),
    ], size=14.5)
    note(slide, "来源：Adobe / Salesforce / QuestMobile（高置信）；公司披露与媒体口径（中置信）。详见预读文档第 1~3 节。")

    # ---- 3 三个建议 ----
    pn += 1
    slide = new_slide(prs, kicker="执行摘要 2/2", title="三个建议：Build 站内助手、Ready 供给就绪、Partner 微信卡位", page_no=pn)
    bullets(slide, [
        ("Build｜90 天在山姆 App/小程序上线『餐桌助手』MVP",
         "菜谱→购物车、常购清单一键成车、商品问答三个高确定场景；深圳/上海会员灰度 10%；KPI：周使用率 ≥15%、助手加购转化 ≥ 搜索基线 1.2 倍"),
        ("Ready｜立即建立 AI 可见度基线与商品数据 LLM 就绪化",
         "500 组购物问题×豆包/千问/元宝/点点，月度监测『山姆被推荐率、被平替率』；500 SKU feed 结构化 POC——所有路线的地基，成本低、无前置条件"),
        ("Partner｜把腾讯云 Mall 合作升级为『山姆 Agent』共建",
         "对标元宝×京东模式卡位微信 AI 入口；谈判底线=交易、会员、支付留在山姆体系（Sparky 原则）；对豆包/千问保持『可被发现、不交交易』的最小接入"),
    ], size=14.5)
    note(slide, "三条并行组合执行而非三选一；预算与团队诉求见第 16 页。")

    # ---- 4~7 全球信号 ----
    pn += 1
    image_slide(prs, "全球信号 1/4", "AI 导流一年成为零售结构性渠道：Q1 同比 +393%，假日季峰值 +1151%",
                "02_us_ai_traffic_growth.png", pn,
                "来源：Adobe Digital Insights（基于美国零售网站超 1 万亿次访问，高置信），2026-04。")
    pn += 1
    image_slide(prs, "全球信号 2/4", "质量逆转：AI 流量转化率从 -38% 到 +42%，单访问收入高 37%",
                "03_ai_conversion_reversal.png", pn,
                "来源：Adobe（高置信）。含义：AI 流量已是最优获客渠道，且当前获取成本低于付费搜索——红利期窗口。")
    pn += 1
    image_slide(prs, "全球信号 3/4", "假日季检验：AI 影响 20% 全球订单；部署自有 Agent 的零售商增速快 59%",
                "06_holiday_ai_influence.png", pn,
                "来源：Salesforce（15 亿+ 消费者样本，高置信）。口径提醒：『AI 影响的销售』≠『AI 内成交』。")
    pn += 1
    image_slide(prs, "全球信号 4/4", "规模预期：口径相差 35 倍——『AI 内成交』尚小，『AI 影响』已巨大",
                "01_global_agentic_forecasts.png", pn,
                "来源：eMarketer / Morgan Stanley / Bain / McKinsey / Edgar Dunn（中置信预测）。决策含义：不必赌宽口径兑现，窄口径已足以支撑试点级投入。")

    # ---- 8 沃尔玛全球已验证 ----
    pn += 1
    slide = new_slide(prs, kicker="全球资产", title="沃尔玛美国已替我们交过学费：代结账失败、插件模式成功", page_no=pn)
    bullets(slide, [
        ("Instant Checkout 教训（2025-10 ~ 2026-03）",
         "约 20 万 SKU 接入 ChatGPT 站内代结账：转化率仅为自有渠道约 1/3、错购频发 → 退出。结论：缺购物车/优惠/会员/库存联动的对话内直购不成立"),
        ("Sparky 插件模式（2026-03 起）",
         "自有 Agent 进驻 ChatGPT（Plus/Pro）与 Gemini：对话内逛沃尔玛、回沃尔玛结账，转化恢复到自有站约 70%，会员与数据完整保留；Claude 集成洽谈中"),
        ("同行印证",
         "Amazon Rufus：2025 年 3 亿+ 用户、购买完成率 +60%、约 120 亿美元增量年化销售（自报，中置信）；Instacart 把 Cart Assistant 白标输出给 Kroger/Sprouts——生鲜 AI 进入『基建即服务』阶段"),
        ("对中国团队的含义",
         "①站内 AI 导购 ROI 为正、②交易主权留自有体系、③『被 AI 发现』是新流量入口——三件事无需在中国重新论证，需要的是本地化入口选择与合规改造"),
    ], size=13.5)
    note(slide, "来源：The Paypers / WIRED 报道、OpenAI 公告（中置信）；关键数字已与多方报道交叉。")

    # ---- 9 中国格局 ----
    pn += 1
    table_slide(prs, "中国战场 1/4", "入口格局：四大阵营已成，微信系联盟模式与沃尔玛通道天然契合", pn,
                ["阵营", "模式", "关键进展（置信度）", "对沃尔玛中国的含义"],
                [
                    ["字节：豆包×抖音", "垂直闭环", "3.83 亿 MAU（高）；『买前问豆包』一级入口，App 内闭环；2026-07 起订单正式归因（中）", "年轻家庭决策截流；『山姆平替』内容放大器"],
                    ["阿里：千问×淘宝", "垂直闭环", "1.66 亿 MAU（高）；对话完成淘宝全链路；1.4 亿用户首次 AI 购物（中）", "盒马为其生鲜抓手，入口优先导流阿里系"],
                    ["腾讯+京东：元宝×京东", "生态联盟", "2026-07 打通小程序生态：对话出商品卡→跳京东小程序成交（中）", "最重要样板：微信 AI 愿以小程序方式与零售方合作——山姆可复制"],
                    ["京东自有 AI", "自建", "京言/京东 AI 购等；自报数据（8000 万用户等）→ 低置信·不采信", "方向可确认、数字不采信；既是秒送渠道伙伴又是竞对"],
                    ["变量：小红书点点 / 拼多多 / 快手", "社区 AI / 站内工具", "点点并入主站（中）；拼多多、快手已上线 AI 搜索，披露极少", "点点=山姆爆品种草与平替拆解主阵地，GEO 必须覆盖"],
                ],
                [2.0, 1.5, 4.6, 3.9],
                "来源：QuestMobile（高）、各公司官宣（中）、京东发布会（低置信·降级）。", font_size=10.5, row_h=0.72)

    # ---- 10 入口规模图 ----
    pn += 1
    image_slide(prs, "中国战场 2/4", "入口体量：豆包已达 3.83 亿月活；京东自报数据以斜纹降级呈现",
                "04_ai_entrance_user_scale.png", pn,
                "红=国内、蓝=海外；斜纹=低置信（自报·注水风险）。WAU/MAU/年度用户/设备数口径各异，仅作量级对照。", img_h=4.55)

    # ---- 11 中国渗透 ----
    pn += 1
    image_slide(prs, "中国战场 3/4", "渗透曲线：AI 私域电商 2025 年 0.65 万亿，2030 年预计 3.37 万亿",
                "05_china_ai_private_ecommerce.png", pn,
                "来源：网经社（中置信）。口径仅为私域子集——中国尚无全量『AI 电商 GMV』权威口径，本研究将自建估算模型。", img_h=4.55)

    # ---- 12 站内导购成绩单 ----
    pn += 1
    image_slide(prs, "中国战场 4/4", "站内 AI 导购已被证明有效：转化提升 40%~60% 是可信区间",
                "07_instore_ai_scorecard.png", pn,
                "绿=第三方/自报效果指标；斜纹=低置信（京东自报）。Rufus 约 120 亿美元增量为亚马逊自报（中置信）。", img_h=4.55)

    # ---- 13 山姆资产盘点 ----
    pn += 1
    table_slide(prs, "沃尔玛中国映射 1/2", "山姆的七项资产决定：AI 导购的 ROI 天花板全行业最高", pn,
                ["资产", "数值/事实（置信度）", "AI 含义"],
                [
                    ["会员体系", "付费会员 1070 万、卓越续卡率 92%（中）", "高质量第一方数据；『替会员省时间』叙事天然成立"],
                    ["精选 SKU", "约 4000 个，为传统商超 1/10", "商品池小 → 推荐准、幻觉少、推理成本低"],
                    ["线上盘", "线上占比超 50%（约 650~700 亿元）；80% 订单 1 小时达（中）", "AI 转化增益直接作用于最大收入池"],
                    ["履约网络", "门店+云仓双层网络，前置仓/云仓 455+（中）", "『餐桌 Agent』的履约兑现现成"],
                    ["供应链 AI", "云仓自动补货指令占比近 90%（中）", "向『损耗联动导购』延伸的边际成本低"],
                    ["腾讯合作", "云 Mall 支撑山姆 App/小程序多年（大促峰值 QPS 10 万+）", "微信 AI 卡位的现成工程与商务通道"],
                    ["全球资产", "Sparky 产品与插件经验、Instant Checkout 教训", "方法论可复用；模型与数据链路须本地合规化"],
                ],
                [1.7, 5.3, 5.0],
                "来源：公司披露、沃尔玛国际管理层披露、媒体报道（中置信）。", font_size=10.5, row_h=0.6)

    # ---- 14 威胁与机会 ----
    pn += 1
    slide = new_slide(prs, kicker="沃尔玛中国映射 2/2", title="四个威胁（按紧迫度）与三个结构性机会", page_no=pn)
    add_textbox(slide, Inches(0.8), Inches(1.6), Inches(5.9), Inches(4.9), [
        ("威胁（紧迫度排序）", 15, True, RED, None),
        ("1. 决策截流（现在进行时）：会员先问豆包/小红书『值不值、有无平替』；爆品是平替内容头号素材", 12.5, False, INK, 0),
        ("2. 即时零售火力升级（1 年内）：美团小象+叮咚约 2000 前置仓 + 成熟算法，对极速达形成价格与时效双压", 12.5, False, INK, 0),
        ("3. 入口绑定排他（1~2 年）：微信 AI 零售位若被京东系独占，沃尔玛在最大社交流量池 AI 化失位", 12.5, False, INK, 0),
        ("4. 供给侧标准缺位（1~2 年）：feed 不做 LLM 就绪化，各 AI 入口可见度被动下降（海外：34% 商品页对 AI 不可见）", 12.5, False, INK, 0),
    ])
    add_textbox(slide, Inches(7.0), Inches(1.6), Inches(5.7), Inches(4.9), [
        ("机会（山姆结构性占优）", 15, True, RGBColor(0x04, 0x78, 0x57), None),
        ("1. 餐桌 Agent：会员制+菜谱驱动+高频复购，『今晚吃什么→一键成车→1 小时达』全中国只有山姆能以自有流量跑通", 12.5, False, INK, 0),
        ("2. 会员复购代理（A4 级）：常购清单自动化、盯价、到货提醒——低 SKU 高复购下授权代理信任门槛最低", 12.5, False, INK, 0),
        ("3. 损耗联动导购：云仓库存/效期接入推荐（临期折扣+今晚特价菜谱），同时改善损耗与体验——直击近期极速达临期品舆情", 12.5, False, INK, 0),
    ])
    note(slide, "对标：Instacart Cart Assistant（膳食规划）已落地 Kroger/Sprouts；能力五级框架（A1 问答 → A5 自主代理）详见预读文档。")

    # ---- 15 战略选项 ----
    pn += 1
    table_slide(prs, "战略选项", "Build / Partner / Ready 组合执行，而非三选一；三条红线不碰", pn,
                ["路线", "内容", "加码判据", "风险控制"],
                [
                    ["Build 自建站内 AI", "山姆 App/小程序『餐桌助手』；国内合规模型栈私有化部署、数据不出域", "站内渗透率与转化增益达标即扩品类、扩沃尔玛 App", "先做高确定任务（复购/菜谱/售后）；低 SKU 使幻觉可控"],
                    ["Partner 生态卡位", "与腾讯共建『山姆 Agent』进微信 AI 场景（对标元宝×京东）", "微信 AI 入口 DAU 与元宝×京东实际成交表现", "底线=交易、会员、支付留在山姆体系；拒绝排他"],
                    ["Ready 供给就绪", "feed 结构化 + 四大入口可见度监测（GEO）+ 支付代扣授权预研", "立即执行，无前置条件", "成本低，情报与数据治理为主"],
                ],
                [1.9, 4.4, 3.0, 2.7],
                "不建议：①把结账交给第三方 AI（全球已证伪）；②在淘宝/抖音竞对生态做深度绑定；③等『中立比价 AI』出现（国内大概率伪命题）。",
                font_size=10.5, row_h=0.78)

    # ---- 16 90天行动 ----
    pn += 1
    table_slide(prs, "行动方案", "90 天三个试点 + 一条谈判线：每项带 KPI 门槛与止损条件", pn,
                ["#", "试点", "范围", "90 天 KPI 门槛", "止损条件"],
                [
                    ["P1", "山姆 App 餐桌助手 MVP", "菜谱→购物车 / 常购清单 / 商品问答；深沪会员灰度 10%", "周使用率 ≥15%；加购转化 ≥ 搜索基线 1.2 倍；客诉率 ≤ 人工", "任一 KPI 连续 4 周 < 门槛 50% → 收缩场景重做"],
                    ["P2", "AI 可见度与平替风险基线", "500 组问题×豆包/千问/元宝/点点月测；500 SKU feed 改造 POC", "产出基线报告与 GEO 优先级清单；改造后可见度提升可测量", "无（纯情报与数据治理投入）"],
                    ["P3", "会员 AI 售后代理", "企微+小程序退换货/效期问题自动化（含临期品场景）", "自动解决率 ≥40%；满意度不降；单均服务成本 -30%", "错误处理率 >2% 即回退人工"],
                    ["N1", "腾讯谈判线", "『山姆 Agent 进微信 AI』联合 POC；明确数据与结账边界", "90 天内达成 POC 范围与商务框架意向", "腾讯排他倾向明显 → 转多入口目录接入"],
                ],
                [0.6, 2.2, 3.6, 3.3, 2.6],
                "资源诉求（CTO 决策）：8~12 人虚拟团队；国内合规模型栈选型（混元/DeepSeek/通义，判据=中文商品理解、推理成本、合规就绪）；第三方数据预算约百万元级/年。",
                font_size=10, row_h=0.8)

    # ---- 17 风险合规 ----
    pn += 1
    slide = new_slide(prs, kicker="风险与合规", title="外资零售在华做 AI 导购的六条红线与应对", page_no=pn)
    bullets(slide, [
        ("生成式 AI 服务合规", "面向公众的 AI 导购须完成生成式 AI 服务备案/算法推荐备案——备案周期前置进项目计划"),
        ("数据出境与模型选型", "会员与对话意图数据不得接入境外模型：国内私有化部署 + 数据不出域；与全球团队『方法论共享、数据隔离』"),
        ("幻觉与错购责任", "低 SKU + 结构化数据源优先；金额敏感操作二次确认；错误率红线 2%"),
        ("未成年人与代扣授权", "A4 级自动购买默认关闭，会员主动开启 + 额度管控（豆包不做全自动下单的原因即在此）"),
        ("比价与价格表述", "只承诺『山姆内最优方案』，不做全网比价话术——规避价格法与反不正当竞争风险"),
        ("竞争情报误判", "京东系自报数据注水：若按其口径校准投入，会系统性高估对手、错配预算——本报告已全线降级处理"),
    ], size=13)
    note(slide, "合规项须在 P1 试点立项时同步启动，勿事后补课。")

    # ---- 18 下一步 ----
    pn += 1
    slide = new_slide(prs, kicker="下一步", title="研究计划推进与需要 CTO 的三项支持", page_no=pn)
    bullets(slide, [
        ("研究推进（本报告为 P1+P2 阶段预读版）",
         "P3 产品实测：10 款 AI 导购评测协议（10 任务×6 维度，独立双评审盲评）→ P4 专家访谈 8~10 场（腾讯、美团系、GEO 服务商、支付方）→ P5 终版报告与 PPT"),
        ("质量承诺",
         "终版按《汇报评分标准》执行独立评审盲评循环：作者与评审分离、轮次盲评、逐维打分、证据强制；加权 ≥4.20 且单维 ≥3.5 方可提交（评分记录随附）"),
        ("需要 CTO 支持",
         "①访谈引荐（腾讯智慧零售、全球 Sparky 团队）；②第三方数据预算审批（QuestMobile 等）；③指定业务侧 Sponsor 对齐试点 KPI"),
    ], size=14)
    note(slide, "配套材料：预读文档（约 30 分钟）、评分标准与评分记录、数据底表与图表源文件（可复现）。")

    out_path = OUT / "AI电商行业研究_沃尔玛中国CTO汇报.pptx"
    prs.save(out_path)

    outline_path = OUT / "pptx_outline.md"
    outline_path.write_text(
        "# PPT 文字稿（评审用，自动生成）\n\n"
        "> 由 `scripts/make_pptx.py` 生成；正式内容以 PPTX 为准。\n"
        + "\n".join(outline_lines) + "\n",
        encoding="utf-8",
    )
    print(f"已生成：{out_path.relative_to(ROOT)}（{pn} 页）")
    print(f"已生成：{outline_path.relative_to(ROOT)}")


if __name__ == "__main__":
    build()
