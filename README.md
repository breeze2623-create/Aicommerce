# AI电商行业研究

正式版行业研究报告与可复现图表/PPT。

## 正式交付物

| 文件 | 说明 |
|---|---|
| `report/AI电商行业研究报告.md` | 正式研究报告（九章结构） |
| `report/AI电商行业研究报告.pptx` | 正式版PPT（约20页） |
| `charts/*.png` | 报告配套图表（含来源与口径脚注） |

## 研究计划与方法（配套）

```
docs/
  00_研究计划总览.md
  01_市场数据与图表清单.md
  02_产业链MECE分析.md
  03_零售与生鲜结合点.md
  04_产品与PM机会地图.md
  05_数据源手册与访谈提纲.md
  06_汇报评分标准.md
data/                   # 数据底表（CSV）
scripts/make_charts.py  # 图表生成
scripts/make_pptx.py    # PPT生成
```

## 数据原则

1. 仅采用第三方监测、公司财报或官方公告可追溯数据  
2. 未经独立验证的自报运营数据**不予展示**  
3. 图表脚注须同时标明**数据来源**与**口径说明**  
4. 严格区分「AI影响的销售」与「AI平台内完成的交易」

## 更新方式

```bash
python3 scripts/make_charts.py
python3 scripts/make_pptx.py
```

数据截至 2026-07。
