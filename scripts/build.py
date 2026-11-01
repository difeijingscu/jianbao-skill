# -*- coding: utf-8 -*-
"""content.json -> A4 简报 HTML（1/2/3 页，由版式决定）

用法：
  python build.py content.json [-o out.html] [--layout L1] [--theme T1] [--quiet]

设计：内容是数据，版式是属性。改版式只换 data-layout，改配色只换 data-theme，
      不重新排版、不复制 HTML 正文，从根上消除「残留上一天内容」。
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import config  # noqa: E402

SKELETON = os.path.join(ROOT, "assets", "skeleton.html")
CSS_PATH = os.path.join(ROOT, "assets", "styles.css")

LAYOUTS = {
    "L1": ("双页标准", 2),
    "L2": ("单页精要", 1),
    "L3": ("完整版", 3),
}
THEMES = {"T0": "深蓝橙", "T1": "商务蓝", "T2": "深色科技", "T3": "公文墨"}


# ---------------------------------------------------------------- 渲染：块
def _b(tag, text, cls=None):
    if not text:
        return ""
    c = ' class="%s"' % cls if cls else ""
    return "<%s%s>%s</%s>" % (tag, c, text, tag)


def r_para(b):
    return '<p class="para">%s</p>' % b.get("text", "")


def r_lead(b):
    return ('<div class="lead"><div class="k">%s</div><p>%s</p></div>'
            % (b.get("label", ""), b.get("text", "")))


def r_list(b):
    tag = "ol" if b.get("ordered") else "ul"
    items = "".join("<li>%s</li>" % x for x in b.get("items", []))
    return '<%s class="lst">%s</%s>' % (tag, items, tag)


def r_metrics(b):
    cells = []
    for m in b.get("items", []):
        unit = m.get("unit") or ""
        cells.append('<div class="m"><div class="n">%s<span>%s</span></div>'
                     '<div class="l">%s</div></div>'
                     % (m.get("value", ""), unit, m.get("label", "")))
    return '<div class="metrics">%s</div>' % "".join(cells)


def r_columns(b):
    cols = []
    for c in b.get("items", []):
        lis = "".join("<li>%s</li>" % x for x in c.get("items", []))
        cols.append('<div class="p"><div class="h"><div class="t">%s</div>'
                    '<div class="s">%s</div></div><ul>%s</ul></div>'
                    % (c.get("title", ""), c.get("sub", ""), lis))
    return '<div class="pillars">%s</div>' % "".join(cols)


def r_cards(b):
    cards = []
    for c in b.get("items", []):
        cls = "cd hi" if c.get("hi") else "cd"
        tag = ('<span class="cd-tag">%s</span>' % c["tag"]) if c.get("tag") else ""
        right = ('<span class="cd-r">%s</span>' % c["right"]) if c.get("right") else ""
        cards.append('<div class="%s"><div class="cd-h"><span class="cd-n">%s%s</span>%s</div>'
                     '<div class="cd-v">%s</div></div>'
                     % (cls, tag, c.get("title", ""), right, c.get("text", "")))
    cols = b.get("cols", 2)
    return '<div class="cards" style="--cols:%d">%s</div>' % (cols, "".join(cards))


def r_table(b):
    widths = b.get("widths") or []
    head = ""
    if b.get("head"):
        ths = "".join(
            "<th%s>%s</th>" % ((' style="width:%s"' % widths[i]) if i < len(widths) and widths[i] else "", h)
            for i, h in enumerate(b["head"]))
        head = "<tr>%s</tr>" % ths
    rows = ""
    for row in b.get("rows", []):
        rows += "<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in row)
    return '<table class="kv">%s%s</table>' % (head, rows)


def r_agenda(b):
    w = b.get("widths") or ["19mm", "42mm"]
    style = ' style="--w1:%s;--w2:%s"' % (w[0], w[1] if len(w) > 1 else "42mm")
    rows = ""
    if b.get("head"):
        rows += '<div class="ag-row ag-head">%s</div>' % "".join(
            "<span>%s</span>" % h for h in b["head"])
    for row in b.get("rows", []):
        rows += "<div class=\"ag-row\">%s</div>" % "".join(
            '<span class="%s">%s</span>' % (cls, cell)
            for cls, cell in zip(("ag-t", "ag-n", "ag-s"), row))
    return '<div class="ag"%s>%s</div>' % (style, rows)


def r_bars(b):
    out = []
    for i, it in enumerate(b.get("items", []), 1):
        cls = "crow hi" if it.get("hi") else "crow"
        unit = it.get("unit", "场")
        out.append('<div class="%s"><span class="rk">%d</span><span class="lb">%s</span>'
                   '<span class="bar"><i style="width:%.1f%%"></i></span>'
                   '<span class="vl"><b>%s</b>%s</span></div>'
                   % (cls, i, it.get("label", ""), float(it.get("pct", 0)),
                      it.get("value", ""), unit))
    return '<div class="bars">%s</div>' % "".join(out)


def r_timeline(b):
    nodes = []
    for n in b.get("items", []):
        cls = "node hl" if n.get("hi") else "node"
        tag = ('<span class="tag">%s</span>' % n["tag"]) if n.get("tag") else ""
        stat = ('<div class="st">%s</div>' % n["stat"]) if n.get("stat") else ""
        lis = ""
        if n.get("items"):
            lis = "<ul>%s</ul>" % "".join("<li>%s</li>" % x for x in n["items"])
        # phase：时间注记（阶段词，如「前期 / 当前 / 后续」）；兼容旧字段名 week
        mark = n.get("phase") or n.get("week") or ""
        nodes.append('<div class="%s"><span class="dot"></span>'
                     '<div class="nh"><span class="d">%s</span><span class="w">%s</span>%s</div>'
                     '%s<div class="dc">%s</div>%s</div>'
                     % (cls, n.get("date", ""), mark, tag,
                        stat, n.get("desc", ""), lis))
    return '<div class="tl">%s</div>' % "".join(nodes)


BLOCKS = {
    "para": r_para, "lead": r_lead, "list": r_list, "metrics": r_metrics,
    "columns": r_columns, "cards": r_cards, "table": r_table,
    "agenda": r_agenda, "bars": r_bars, "timeline": r_timeline,
}


# ---------------------------------------------------------------- 渲染：段与页
def r_section(s):
    out = []
    if s.get("part"):
        p = s["part"]
        out.append('<div class="part"><span class="pn">%s</span>'
                   '<span class="pt">%s</span><span class="pd">%s</span></div>'
                   % (p.get("no", ""), p.get("title", ""), p.get("sub", "")))
    head = '<div class="sec-t">%s' % s.get("title", "")
    if s.get("sub"):
        head += "<em>%s</em>" % s["sub"]
    head += "</div>"
    body = ""
    for b in s.get("blocks", []):
        fn = BLOCKS.get(b.get("type", ""))
        if fn is None:
            config.out("WARN 未知 block 类型：%r（section %s），已跳过"
                       % (b.get("type"), s.get("title")))
            continue
        body += fn(b)
    out.append('<section class="sec">%s%s</section>' % (head, body))
    return "".join(out)


def r_header(d):
    m = d.get("meta", {})
    hl = d.get("headline") or {}
    kicker = '<div class="kicker">%s</div>' % m.get("kicker", "")
    if m.get("kicker_note"):
        kicker += '<div class="kicker em">%s</div>' % m["kicker_note"]
    title = "<h1>%s" % m.get("title", "")
    if m.get("subtitle"):
        title += '<span class="sb">%s</span>' % m["subtitle"]
    title += "</h1>"
    meta_line = "　|　".join(m.get("meta_line", []))
    if m.get("author"):
        meta_line += "<br>%s" % m["author"]
    one = ""
    if hl.get("text"):
        one = ('<div class="oneline"><span class="ol-k">%s</span>'
               '<span class="ol-v">%s</span></div>'
               % (hl.get("label", "核心判断"), hl["text"]))
    return ('<header><div class="brandrow">%s</div>%s<div class="meta">%s</div>%s</header>'
            % (kicker, title, meta_line, one))


def r_footer(d):
    note = d.get("note") or ""
    srcs = ""
    if d.get("sources"):
        srcs = '<div class="src-list">%s</div>' % "".join(
            "<span>[%d] %s · %s%s</span>"
            % (i, s.get("publisher", ""), s.get("title", ""),
               (" · " + s["date"]) if s.get("date") else "")
            for i, s in enumerate(d["sources"], 1))
    note_html = ('<div class="note"><b>数据口径与信源：</b>%s%s</div>' % (note, srcs)) if (note or srcs) else ""
    ft = ('<footer><span>%s</span><span>%s</span></footer>'
          % (d.get("footer_left", ""), d.get("footer_note", "")))
    return note_html + ft


# ---------------------------------------------------------------- 主流程
def pick_sections(data, layout):
    max_p = LAYOUTS[layout][1]
    kept, dropped = [], []
    for s in data.get("sections", []):
        (kept if int(s.get("p", 2)) <= max_p else dropped).append(s)
    return kept, dropped


def build(data, layout="L1", theme="T0"):
    if layout not in LAYOUTS:
        raise SystemExit("未知版式 %s，可选：%s" % (layout, "/".join(LAYOUTS)))
    if theme not in THEMES:
        raise SystemExit("未知配色 %s，可选：%s" % (theme, "/".join(THEMES)))

    kept, dropped = pick_sections(data, layout)

    pages = {}
    if layout == "L2":
        # 单页精要：所有保留段落压到第 1 页，page 字段忽略
        pages = {1: kept}
    else:
        for s in kept:
            pages.setdefault(int(s.get("page", 1)), []).append(s)
    if not pages:
        raise SystemExit("content.json 里没有可用 section（检查 p 字段与版式是否匹配）")

    order = sorted(pages)
    html_pages = []
    for idx, pno in enumerate(order):
        inner = ""
        if idx == 0:
            inner += r_header(data)
        inner += "".join(r_section(s) for s in pages[pno])
        if idx == len(order) - 1:
            inner += r_footer(data)
        html_pages.append('<div class="page">%s</div>' % inner)

    css = open(CSS_PATH, encoding="utf-8").read()
    sk = open(SKELETON, encoding="utf-8").read()
    html = (sk.replace("{{CSS}}", css)
              .replace("{{PAGES}}", "\n".join(html_pages))
              .replace("{{THEME}}", theme)
              .replace("{{LAYOUT}}", layout)
              .replace("{{TITLE}}", data.get("meta", {}).get("title", "简报")))
    return html, dropped


def slug(text, n=20):
    s = re.sub(r"[^\w\u4e00-\u9fa5]+", "", text or "")
    return (s[:n] or "简报")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        raise SystemExit(1)
    src = args[0]
    layout = "L1"
    theme = "T0"
    out_path = None
    quiet = "--quiet" in args
    for i, a in enumerate(args):
        if a == "--layout" and i + 1 < len(args):
            layout = args[i + 1].upper()
        if a == "--theme" and i + 1 < len(args):
            theme = args[i + 1].upper()
        if a in ("-o", "--out") and i + 1 < len(args):
            out_path = args[i + 1]

    data = json.loads(open(src, encoding="utf-8-sig").read())
    html, dropped = build(data, layout, theme)

    if not out_path:
        m = data.get("meta", {})
        out_path = "简报-%s-%s-%s-%s-%s.html" % (
            slug(m.get("topic") or m.get("title")),
            (m.get("date") or "").replace("-", "") or "undated",
            layout, theme, THEMES[theme])
    out_path = os.path.abspath(out_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    open(out_path, "w", encoding="utf-8").write(html)

    if not quiet:
        config.out("HTML -> %s" % out_path)
        config.out("版式=%s(%s) 配色=%s(%s) 段数=%d 页数=%d"
                   % (layout, LAYOUTS[layout][0], theme, THEMES[theme],
                      len(data.get("sections", [])) - len(dropped),
                      html.count('class="page"')))
        if dropped:
            config.out("本版式省略 %d 段（p 优先级高于上限）：%s"
                       % (len(dropped), " / ".join(s.get("title", "?") for s in dropped)))
    return out_path


if __name__ == "__main__":
    main()
