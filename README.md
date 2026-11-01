# jianbao — Executive Brief Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)

**Turn any topic into a 1–3 page A4 executive brief: researched, sourced, and typeset. One JSON file, three layouts, four color themes, HTML + PDF out.**

简体中文说明见 [README.zh-CN.md](README.zh-CN.md)。

---

Most "generate a report with AI" pipelines end in one of two places: a wall of markdown that nobody prints, or an HTML template that gets hand-edited until the numbers drift. `jianbao` takes a third route — **content is data, layout is an attribute**:

- The agent writes a single `content.json` (facts, numbers, sources, prose).
- `build.py` renders it into a fixed A4 grid, choosing which sections to keep based on a priority field.
- Switching style changes `data-layout` / `data-theme` — never the prose. Nothing from the previous run can leak into the next one.

The two gates are non-negotiable: **layout overflow must be 0px, and content validation must return 0 errors** before anything is delivered.

## Showcase

All four images are rendered from the same `assets/example/content.json` (fictional sample data) — same content, different style.

| Standard 2-page · Business Blue (`L1` / `T1`) | Page 2 |
|---|---|
| ![L1 page 1](docs/images/l1-t1_p1.png) | ![L1 page 2](docs/images/l1-t1_p2.png) |

| One-page digest · Dark Tech (`L2` / `T2`) | Full edition · Official Ink (`L3` / `T3`) |
|---|---|
| ![L2](docs/images/l2-t2_p1.png) | ![L3](docs/images/l3-t3_p1.png) |

## Requirements

- **Python 3.8+** — standard library only, no `pip install`.
- **A Chromium-based browser** (Chrome / Chromium / Edge) for layout measurement and PDF export.
  Auto-detected on Windows, macOS and Linux; override with `JB_BROWSER=/path/to/chrome`.
- **CJK fonts** for non-Chinese systems: `apt-get install fonts-noto-cjk` on Debian/Ubuntu.

## Install

This repo follows the `SKILL.md` convention, so it works in two ways.

**As an agent skill** (WorkBuddy and compatible hosts) — put it where your host looks for skills:

```bash
git clone https://github.com/difeijingscu/jianbao-skill.git
cp -r jianbao-skill ~/.workbuddy/skills/jianbao   # directory name must be jianbao
```

Then just ask: *"给老板做一份 AI 芯片出口管制简报"*. The agent loads the skill, asks for layout and theme, researches, writes `content.json`, renders, and runs both gates.

**As a plain CLI** — the scripts have no agent dependency:

```bash
python scripts/new_brief.py ./my-brief --topic "AI芯片出口管制" --title "AI芯片出口管制：执行口径出现分化"
python scripts/build.py my-brief/content.json --layout L1 --theme T1
python scripts/check_layout.py 简报-*.html
python scripts/validate.py my-brief/content.json --html 简报-*.html
python scripts/to_pdf.py 简报-*.html
```

## The five steps

```
0. confirm   scope + time window · layout · theme        (only what's unclear)
1. scaffold  new_brief.py      → content.json with TODOs
2. research  ≥3 independent sources, every number traced to its origin
3. write     content.json      3–10 sections, each tagged p=1|2|3
4. render    build.py          → A4 HTML
5. gate      check_layout.py   overflow = 0, fill rate ≥ 62%
             validate.py       0 ERROR
   deliver   to_pdf.py         → PDF
```

`validate.py` rejects the scaffold's `TODO`s on purpose: an unfilled skeleton cannot be delivered.

## Layouts and themes

Layouts are **structural** — they decide which sections survive. Themes are **purely cosmetic**.

| Code | Layout | Sections kept | Use |
|---|---|---|---|
| `L2` | One-page digest | `p=1` only | three minutes before a meeting |
| `L1` | Two-page standard | `p≤2` | default delivery |
| `L3` | Full edition | all | archiving, terminology, extended notes |

| Code | Theme | Use |
|---|---|---|
| `T1` | Business Blue | print, B&W photocopy, formal submission (default) |
| `T0` | Navy & Orange | on-screen circulation, high contrast |
| `T3` | Official Ink | government/formal style, greyscale + dark red |
| `T2` | Dark Tech | projection; ink-heavy, not for printing |

Switching **theme** is in-place: `restyle.py brief.html --theme T2 --pdf`.
Switching **layout** must re-render: `build.py content.json --layout L2`. `restyle.py --layout` refuses and tells you the right command — layout filtering happens at render time, so it cannot be done by CSS.

## Block types

| `type` | Purpose | Key fields |
|---|---|---|
| `lead` | headline judgement, dark band | `label` `text` |
| `metrics` | 3–4 key numbers | `items[].value/unit/label` |
| `list` | numbered or bulleted points | `items` `ordered` |
| `cards` | parallel viewpoints, 2–3 columns | `cols` `items[].title/right/tag/text/hi` |
| `columns` | three-column contrast (impact / action / open) | `items[].title/sub/items` |
| `table` | quantified metrics, side-by-side comparison | `head` `widths` `rows` |
| `agenda` | timetable (time / party / content) | `head` `widths` `rows` |
| `bars` | share and heat distribution | `items[].label/value/pct/hi` |
| `timeline` | sequence of developments | `items[].date/phase/tag/stat/desc/items` |

Inline `<b>` and `<br>` are allowed in prose; `<script>`, `<style>` and `on*=` are rejected by `validate.py`.

## What the validator actually checks

`check_layout.py` answers "was anything silently cut off?" — `.page` is a fixed `297mm` with `overflow: hidden`, so overflow disappears without an error. It also reports **fill rate**, because a page that is only 60% full is a different failure that overflow checks miss.

`validate.py` covers what a visual check cannot:

- required fields, section count, block schema
- leftover placeholders (`TODO`, `待补`, `{{`)
- page count vs. layout ceiling
- metric values that never appear in the body text (a reliable signal of inconsistent denominators)
- **period labels in titles** — `Day2`, `第 2 天`, `第 3 期` are rejected, because a brief is named after its topic, not after a day of some multi-day event

## Repository layout

```
SKILL.md                      the skill spec: rules, workflow, block reference
assets/
  skeleton.html               page shell, placeholders only — no sample content
  styles.css                  all styling: CSS variables × layouts
  example/content.json        fictional sample, used by the screenshots above
references/
  content-spec.md             every field of content.json + writing rules
  source-policy.md            source tiers, verification order, number discipline
  troubleshooting.md          environment requirements and known issues
scripts/
  new_brief.py                scaffold content.json
  build.py                    content.json → HTML
  check_layout.py             overflow + fill-rate measurement (headless Chrome)
  validate.py                 structure, placeholders, naming, number consistency
  to_pdf.py                   HTML → A4 PDF
  restyle.py                  switch theme in place
  config.py                   browser / temp-dir detection
docs/images/                  screenshots
```

## Adding a theme

Themes are CSS variables, so a new one is about 12 lines in `assets/styles.css`:

```css
[data-theme="T4"] {
  --bg: #ffffff; --fg: #1a1a1a; --ink-2: #3d3d3d; --ink-3: #6b6b6b; --ink-4: #8f8f8f;
  --line: #dcdcdc; --panel: #f5f6f8; --brand: #0f5c4a; --brand-ink: #0f5c4a; --lead-mark: #0f5c4a;
}
```

Register the code in `build.py` (`THEMES`) and `restyle.py` (`THEMES`) and it appears in the CLI.

## Design notes

- **No `!important` overrides.** Earlier iterations themed by rewriting every class name; any layout change silently broke theming. Variables fixed that.
- **No sample content in the skeleton.** A template carrying last run's numbers is how wrong figures get copied forward.
- **Fill the page with information, not whitespace.** When fill rate is low, add a substantive section or drop to a smaller layout — never stretch spacing with `space-between`.
- **Numbers carry their denominator.** Every figure in a brief states its scope, window and source; the footer block records all of them.

## License

MIT — see [LICENSE](LICENSE). The sample content in `assets/example/content.json` is fictional and for layout validation only.
