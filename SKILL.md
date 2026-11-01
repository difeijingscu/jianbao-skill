---
name: jianbao
description: 把用户指定范围（某主题、某展会、某事件、某公司动态、某政策）的公开信息，广泛检索核实后写成给高层看的中文简报——固定 A4 版式，1–3 页，输出 HTML + PDF。支持版式（单页精要 / 双页标准 / 完整版）与配色（商务蓝 / 深蓝橙 / 公文墨 / 深色科技）自由切换，由用户选择。适用于「给老板做一份 XX 简报」「出一份 XX 展会观察」「整理一份 XX 事件通报」「把 XX 主题做成高层速览」「写一份给管理层的行业周报」等需求。
agent_created: true
---

# 高层简报（jianbao）

把任意范围的公开信息，压成 1–3 页高管可读的 A4 简报。核心设计：**内容是数据（content.json），版式是属性（data-layout / data-theme）**——换风格不重排正文，也不会残留上一次的内容。

## 铁律

1. **先定范围再动手。** 范围、时间窗、读者用途不清，最多问 2 个问题，然后按假设出初版。
2. **标题按主题定名。** 简报名 = 用户给的主题 + 判断或观察角度（`<主题>：<结论>`），不写 Day1 / 第 2 天 / 第 3 期这类期次编号——那是特定多日会议才有的写法，不通用。同一主题持续跟踪时，靠 `meta.date` 与文件名日期区分。
3. **事实必须有源。** 无信源的推断不写入；拿不准标注「待确认」。数字必须带口径（统计范围、时间窗、来源）。
4. **不编造。** 数字、引文、日期、机构名一律不得虚构。检索不到就写「未检索到公开信息」，不猜。
5. **两道闸门必须都过**：`check_layout.py` 溢出=0；`validate.py` 0 ERROR。
6. **不改生成的 HTML。** 内容只改 `content.json`，样式只改属性；手改 HTML 会在下次渲染时被覆盖。

## 流程

### 0. 确认三件事

用 AskUserQuestion 一次问清，已明确的不要重复问：

| 项 | 选项 |
|---|---|
| 范围与时间窗 | 由用户给；含糊时给出你推断的范围让其确认 |
| 版式 | **L1 双页标准**（推荐）/ L2 单页精要 / L3 完整版 |
| 配色 | **T1 商务蓝**（推荐，打印友好）/ T0 深蓝橙 / T3 公文墨 / T2 深色科技 |

### 1. 建项目

```bash
python scripts/new_brief.py <目录> --topic "主题短名" --title "主题：一句判断" --date 2026-10-31
```

产出 `<目录>/content.json` 骨架。骨架里全是 TODO——这是故意的，`validate.py` 会拦下未填内容。
`--title` 不填时默认「<主题短名> 简报」，随后应改成 `<主题>：<判断>`（见下方「命名」）。

### 2. 检索（决定简报质量的一步）

- **广度**：至少 3 个互相独立的信源；覆盖面 = 官方/一手 + 权威媒体 + 必要的行业侧信息。
- **深度**：每个关键数字找到原始出处，不用二手转述的数字。
- **记录**：边查边把 `publisher / title / date / url` 写进 `sources`，不要事后补。
- 信源分级、核实顺序、时效标注规则见 `references/source-policy.md`。

### 3. 写 content.json

结构、字段、写作规范见 `references/content-spec.md`。最小要点：

- `headline.text` 90–130 字，结构 = **发生了什么 → 意味着什么 → 一句收口**，结论用 `<b>` 标出。
- `sections` 3–10 段，`p` 字段是优先级（1 必备 / 2 标准 / 3 扩展），决定版式取舍。
- 讲对比、讲量化的内容用 `table`；讲顺序、讲进展用 `timeline`；讲多条并列观点用 `cards`。
- 观点只写有明确公开表述的，**保持原话口径**，不要自行改写或去掉限定语。

### 4. 生成

```bash
python scripts/build.py content.json --layout L1 --theme T1
# 不给 -o 时自动命名为：简报-<主题>-<YYYYMMDD>-<版式>-<配色>.html
```

### 5. 体检（两道闸门）

```bash
python scripts/check_layout.py <html>                  # 溢出=0；填充率≥62%
python scripts/validate.py content.json --html <html>  # 0 ERROR
```

- **溢出**：移动整块到下一页 → 收紧行距 → 微调边距，顺序不可颠倒，**不许缩字号硬塞**。
- **填充率低**：补内容，或换小版式（L2），不要用 `space-between` 把版面撑满。
- 有 WARN 逐条判断：`W4`（指标值未在正文出现）通常意味着口径前后不一致，必须处理。

### 6. 交付

```bash
python scripts/to_pdf.py <html>                    # HTML → A4 PDF
python scripts/restyle.py <html> --theme T2 --pdf  # 只换配色：原地改属性，秒出
python scripts/build.py content.json --layout L2 --theme T1   # 换版式：重新筛段后重建
```

**换版式必须重建，不能原地改。** 版式决定保留哪些段落，是渲染期筛选；配色才是纯 CSS。
用户想在几种风格间挑，就并行生成 2–3 个变体一次给齐，别来回问。

交付时同时给出 HTML 与 PDF，并说明：版式、配色、信息截止时间、哪些结论是「待确认」。

## 版式与配色

**版式**（结构差异，靠 `p` 优先级筛选段落，不重排正文）

| 代号 | 名称 | 保留段落 | 适用 |
|---|---|---|---|
| L2 | 单页精要 | 仅 p=1 | 领导会前 3 分钟看完；结论 + 数字 + 建议 |
| L1 | 双页标准 | p≤2 | 默认交付形态；事实 + 数据 + 影响 |
| L3 | 完整版 | 全部 | 需要留档、含术语与扩展说明 |

**配色**（同一份内容换皮，不改结构）

| 代号 | 名称 | 适用 |
|---|---|---|
| T1 | 商务蓝 | 打印、黑白复印、正式呈报（默认） |
| T0 | 深蓝橙 | 屏幕传阅，对比强 |
| T3 | 公文墨 | 公文风格，黑白灰 + 暗红 |
| T2 | 深色科技 | 投屏演示；费墨，不建议打印 |

## 区块类型

| type | 用途 | 关键字段 |
|---|---|---|
| `lead` | 总判断（深色/浅色横条） | `label` `text` |
| `metrics` | 3–4 个关键数字 | `items[].value/unit/label` |
| `list` | 编号或无序要点 | `items` `ordered` |
| `cards` | 并列观点/术语，2–3 列 | `cols` `items[].title/right/tag/text/hi` |
| `columns` | 三栏对照（影响/建议/待确认） | `items[].title/sub/items` |
| `table` | 量化指标、横向对比 | `head` `widths` `rows` |
| `agenda` | 议程、日程（时间/主体/内容三列） | `head` `widths` `rows` |
| `bars` | 占比/热度分布 | `items[].label/value/pct/hi` |
| `timeline` | 进展脉络 | `items[].date/phase/tag/stat/desc/items` |

正文允许内联 `<b>` `<br>`，**不允许** `<script>`、`<style>`、`on*=`（`validate.py` 会拦）。

## 文件

- `assets/skeleton.html` — 页面骨架（只有占位标记，无任何示例内容）
- `assets/styles.css` — 全部样式（CSS 变量驱动主题；`[data-layout]` 驱动版式）
- `assets/example/content.json` — 虚构示例，验证版式用；同时是 content.json 的写法参照
- `scripts/new_brief.py` — 生成 content.json 骨架
- `scripts/build.py` — content.json → HTML
- `scripts/check_layout.py` — 溢出 + 填充率体检
- `scripts/validate.py` — 结构、占位符、页数、命名、数字自洽体检
- `scripts/to_pdf.py` — HTML → A4 PDF
- `scripts/restyle.py` — 换配色（改 `data-theme`，不动正文）
- `scripts/config.py` — 浏览器路径与临时目录探测
- `references/content-spec.md` — `content.json` 全字段与写作规范
- `references/source-policy.md` — 信源分级、核实顺序、数字纪律
- `references/troubleshooting.md` — 环境要求与已知问题

## 环境

- **Python 3.8+**，只用标准库，无需 `pip install`。
- **Chromium 内核浏览器**（Chrome / Chromium / Edge）用于体检与出 PDF；路径自动探测，自定义安装用 `JB_BROWSER` 指定。
- Linux 缺中文字体会渲染成方框：`apt-get install fonts-noto-cjk`。
- 已知问题（内容被静默裁掉、填充率误判、PDF 多页眉、中文乱码）见 `references/troubleshooting.md`。

## 命名

**标题**：`<主题>：<判断或观察角度>`，如「智能制造装备展：整线交付成为竞争主线」。
按用户给的主题命名，**不出现 Day1 / Day2 / 第 2 天 / 第 3 期**。同一主题出第二份，标题可沿用、结论可更新，用 `meta.date` 和文件名日期区分期次。

**文件**：`简报-<主题>-<YYYYMMDD>-<版式代号>-<配色代号>-<配色名>.html/.pdf`，如 `简报-AI芯片出口管制-20261031-L1-T1-商务蓝.pdf`。
`build.py` / `restyle.py` 自动按此规则命名，不要在页面内容里写「版式 A」之类标识。
