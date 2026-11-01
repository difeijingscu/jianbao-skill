# -*- coding: utf-8 -*-
"""交付前内容体检：结构、占位符残留、页数、数字自洽

用法：
  python validate.py <content.json> [--html 生成物.html] [--allow-period]

退出码：0 通过（可能有 WARN）；1 有 ERROR。
设计意图：排版体检（check_layout.py）只管「有没有被裁掉」，
          本脚本管「内容对不对、有没有半成品残留」。

命名约定：标题/刊头/段名按主题定名，不写 Day1 / 第 2 天这类期次编号。
          确有按天分期的场景（如逐日跟踪的展会日报）加 --allow-period 放行。
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import config  # noqa: E402

PLACEHOLDERS = ["TODO", "待填", "待补", "XX 公司", "示例内容", "{{", "}}", "…略"]
MAX_PAGES = {"L1": 2, "L2": 1, "L3": 4}
# 期次编号：Day2 / DAY 3 / 第 2 天 / 第 3 日 / D1
PERIOD_PAT = re.compile(r"day\s*\d+|第\s*[一二三四五六七八九十\d]+\s*[天日]|\bd[1-9]\b", re.I)

errors, warns = [], []


def err(code, msg):
    errors.append("[%s] %s" % (code, msg))


def warn(code, msg):
    warns.append("[%s] %s" % (code, msg))


def text_of(blocks):
    buf = []
    for b in blocks:
        for k in ("text", "label", "title", "sub"):
            if isinstance(b.get(k), str):
                buf.append(b[k])
        for k in ("items", "rows"):
            if isinstance(b.get(k), list):
                for it in b[k]:
                    if isinstance(it, str):
                        buf.append(it)
                    elif isinstance(it, dict):
                        buf.extend(str(v) for v in it.values() if isinstance(v, str))
                    elif isinstance(it, list):
                        buf.extend(str(x) for x in it)
    return " ".join(buf)


def check_json(data):
    meta = data.get("meta") or {}
    if not meta.get("title"):
        err("E1", "meta.title 缺失")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(meta.get("date", ""))):
        err("E2", "meta.date 必须是 YYYY-MM-DD，当前为 %r" % meta.get("date"))
    if not meta.get("meta_line"):
        err("E3", "meta.meta_line 缺失（范围 / 周期 / 信息截止）")
    if not (data.get("headline") or {}).get("text"):
        err("E4", "headline.text 缺失（页眉核心判断为强制区块）")

    hl = (data.get("headline") or {}).get("text", "")
    n = len(re.sub(r"<[^>]+>", "", hl))
    if hl and not (55 <= n <= 240):
        warn("W1", "headline.text 长度 %d 字，建议 60–200 字（两行为宜）" % n)

    secs = data.get("sections") or []
    if len(secs) < 3:
        err("E5", "sections 少于 3 段，无法支撑高管简报")
    pages = []
    for i, s in enumerate(secs, 1):
        if not s.get("title"):
            err("E6", "第 %d 段缺 title" % i)
        if not s.get("blocks"):
            err("E6", "第 %d 段「%s」blocks 为空" % (i, s.get("title", "")))
        pages.append(int(s.get("page", 1)))
        for b in s.get("blocks", []):
            if b.get("type") == "bars":
                for it in b.get("items", []):
                    if not (0 <= float(it.get("pct", -1)) <= 100):
                        err("E7", "段「%s」条形图 pct 越界：%s" % (s.get("title"), it.get("pct")))
    if pages:
        span = set(pages)
        missing = [p for p in range(min(span), max(span) + 1) if p not in span]
        if missing:
            err("E8", "页码出现空洞 %s（段落的 page 字段不连续，会导致空页）" % missing)

    srcs = data.get("sources") or []
    if len(srcs) < 3:
        err("E9", "sources 少于 3 条（高层简报要求每个关键结论可回溯）")
    for i, s in enumerate(srcs, 1):
        if not s.get("publisher") or not s.get("title"):
            err("E10", "第 %d 条信源缺 publisher 或 title" % i)
        if not s.get("date"):
            warn("W2", "第 %d 条信源缺日期（时效信息应标来源与时效）" % i)

    if not data.get("note"):
        err("E11", "note 缺失（数据口径说明是强制区块）")
    if not (data.get("footer_note") or "").strip():
        warn("W3", "footer_note 为空，页脚「生成时间」建议补真实时间")

    # 占位符残留
    blob = json.dumps(data, ensure_ascii=False)
    for ph in PLACEHOLDERS:
        if ph in blob:
            err("E12", "发现占位符残留：%r" % ph)

    # 数字自洽：metrics 里的数字应在正文出现
    body = " ".join(text_of(s.get("blocks", [])) for s in secs)
    body = re.sub(r"<[^>]+>", "", body)
    for s in secs:
        for b in s.get("blocks", []):
            if b.get("type") == "metrics":
                for m in b.get("items", []):
                    v = str(m.get("value", "")).strip()
                    if v and re.search(r"\d", v) and v not in body:
                        warn("W4", "指标值 %s（%s）未在正文出现，确认是否口径不一致"
                             % (v, m.get("label", "")))


def check_naming(data, allow_period=False):
    """标题/刊头/段名按主题定名，不允许期次编号（DayN / 第N天）"""
    if allow_period:
        return
    meta = data.get("meta") or {}
    fields = [(k, meta.get(k, "")) for k in ("title", "topic", "kicker", "subtitle")]
    for i, s in enumerate(data.get("sections") or [], 1):
        fields.append(("第 %d 段标题" % i, s.get("title", "")))
        if isinstance(s.get("part"), dict):
            fields.append(("第 %d 段横幅" % i, s["part"].get("title", "")))
    for name, v in fields:
        m = PERIOD_PAT.search(str(v or ""))
        if m:
            err("E19", "%s 含期次编号「%s」：简报按主题定名（<主题>：<判断/观察角度>），"
                       "持续跟踪同一主题靠 meta.date 与文件名日期区分" % (name, m.group(0)))


def check_html(path):
    html = open(path, encoding="utf-8").read()
    layout = (re.search(r'data-layout="([^"]*)"', html) or [None, "L1"])[1]
    n_pages = html.count('class="page"')
    limit = MAX_PAGES.get(layout, 2)
    if n_pages > limit:
        err("E13", "版式 %s 最多 %d 页，实际 %d 页" % (layout, limit, n_pages))
    if n_pages < 1:
        err("E14", "未渲染出任何页面")
    if "{{" in html or "}}" in html:
        err("E15", "HTML 残留未替换的模板标记 {{ }}")
    if re.search(r"<script", html, re.I):
        err("E16", "HTML 含 <script>（打印件不应带脚本）")
    for bad in ("javascript:", "onerror=", "onclick="):
        if bad in html.lower():
            err("E17", "HTML 含可疑内联代码：%s" % bad)
    for ph in PLACEHOLDERS:
        if ph in html:
            err("E18", "HTML 发现占位符残留：%r" % ph)
    # 主题/版式属性必须存在
    if 'data-theme="' not in html:
        warn("W5", "缺少 data-theme，将回落到默认配色")
    config.out("HTML 检查：版式=%s 页数=%d" % (layout, n_pages))


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        raise SystemExit(1)
    data = json.loads(open(args[0], encoding="utf-8-sig").read())
    check_json(data)
    check_naming(data, allow_period="--allow-period" in args)
    if "--html" in args:
        check_html(args[args.index("--html") + 1])

    for w in warns:
        config.out("WARN  " + w)
    for e in errors:
        config.out("ERROR " + e)
    if errors:
        config.out("---- 未通过：%d ERROR / %d WARN" % (len(errors), len(warns)))
        raise SystemExit(1)
    config.out("---- 通过：0 ERROR / %d WARN" % len(warns))
    return 0


if __name__ == "__main__":
    main()
