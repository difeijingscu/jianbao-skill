# -*- coding: utf-8 -*-
"""新建一份简报项目：生成 content.json 骨架（结构齐全、内容待填）

用法：
  python new_brief.py <目录> [--topic "主题名"] [--title "标题"] [--date 2026-10-31]

产出：<目录>/content.json
骨架里的 TODO 会被 validate.py 拦下，填完才能交付——这是故意的。
标题按主题定名（<主题>：<判断/观察角度>），不写 Day1 / 第 2 天这类期次编号。
"""
import json
import os
import sys

SKELETON = {
    "meta": {
        "topic": "TODO 主题短名（用于文件名）",
        "kicker": "TODO 英文/正式刊头，如 INDUSTRY WATCH 2026",
        "kicker_note": "内部简报 · 供高层参阅",
        "title": "TODO 标题：<主题>：<判断或观察角度>（≤28 字，不写 DayN / 第N天）",
        "subtitle": "TODO 一句话副标题：这份简报回答什么问题",
        "meta_line": ["范围：TODO", "周期：TODO", "信息截至 TODO"],
        "author": "TODO 整理方",
        "date": "TODO YYYY-MM-DD",
    },
    "headline": {
        "label": "核心判断",
        "text": "TODO 一句话结论：先用 90–130 字说清「发生了什么 → 意味着什么」，"
                "关键结论用 <b>加粗</b> 收口。",
    },
    "sections": [
        {
            "no": "01", "title": "核心事实与进展",
            "sub": "信息源：TODO（媒体 / 官方 / 一手）",
            "page": 1, "p": 1,
            "blocks": [
                {"type": "lead", "label": "总判断", "text": "TODO 2–4 句说清全局判断"},
                {"type": "metrics", "items": [
                    {"value": "TODO", "unit": "", "label": "TODO 指标名"},
                    {"value": "TODO", "unit": "", "label": "TODO 指标名"},
                    {"value": "TODO", "unit": "", "label": "TODO 指标名"},
                ]},
                {"type": "list", "ordered": True, "items": [
                    "TODO 事实 1（带数字与时间）",
                    "TODO 事实 2",
                    "TODO 事实 3",
                ]},
            ],
        },
        {
            "no": "02", "title": "关键数据",
            "sub": "口径见文末说明",
            "page": 1, "p": 1,
            "blocks": [
                {"type": "table", "head": ["项目", "关键数据", "业务含义"],
                 "widths": ["34mm", "52mm", ""],
                 "rows": [["TODO", "<b>TODO</b>", "TODO"]]},
            ],
        },
        {
            "no": "03", "title": "主要观点与信号",
            "sub": "只写有信源的公开表态",
            "page": 1, "p": 2,
            "blocks": [
                {"type": "cards", "cols": 2, "items": [
                    {"title": "TODO 观点 A", "right": "来源 · 场合",
                     "text": "TODO 归纳，勿改写原话口径"},
                    {"title": "TODO 观点 B", "right": "来源 · 场合",
                     "text": "TODO"},
                ]},
            ],
        },
        {
            "no": "04", "title": "对我们的影响与建议",
            "sub": "按可执行动作写，不写口号",
            "page": 2, "p": 1,
            "blocks": [
                {"type": "columns", "items": [
                    {"title": "影响", "sub": "SHORT", "items": ["TODO", "TODO"]},
                    {"title": "建议", "sub": "ACTIONS", "items": ["TODO", "TODO"]},
                    {"title": "待确认", "sub": "OPEN", "items": ["TODO"]},
                ]},
            ],
        },
        {
            "no": "05", "title": "风险与不确定性",
            "sub": "明确写出置信度",
            "page": 2, "p": 2,
            "blocks": [
                {"type": "list", "items": [
                    "TODO 风险 1（高/中/低）",
                    "TODO 风险 2",
                ]},
            ],
        },
        {
            "no": "06", "title": "术语与背景速查",
            "sub": "供非专业读者对齐概念",
            "page": 2, "p": 3,
            "blocks": [
                {"type": "cards", "cols": 2, "items": [
                    {"title": "TODO 术语", "text": "TODO 一句话解释"},
                ]},
            ],
        },
    ],
    "note": "TODO 数据口径说明：每个数字的来源、统计口径、时间窗口；"
            "哪部分为推断、哪部分已核实。",
    "sources": [
        {"publisher": "TODO 媒体/机构", "title": "TODO 文章或公告标题",
         "date": "TODO YYYY-MM-DD", "url": "TODO"},
        {"publisher": "TODO", "title": "TODO", "date": "TODO", "url": "TODO"},
        {"publisher": "TODO", "title": "TODO", "date": "TODO", "url": "TODO"},
    ],
    "footer_left": "TODO 编制方 / 保密级别",
    "footer_note": "生成时间：TODO",
}


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        raise SystemExit(1)
    target = os.path.abspath(args[0])
    data = json.loads(json.dumps(SKELETON))
    for i, a in enumerate(args):
        if a == "--topic" and i + 1 < len(args):
            data["meta"]["topic"] = args[i + 1]
            data["meta"]["title"] = "%s 简报" % args[i + 1]
        if a == "--title" and i + 1 < len(args):
            data["meta"]["title"] = args[i + 1]
        if a == "--date" and i + 1 < len(args):
            data["meta"]["date"] = args[i + 1]

    os.makedirs(target, exist_ok=True)
    path = os.path.join(target, "content.json")
    if os.path.exists(path):
        print("已存在，未覆盖：%s" % path)
        raise SystemExit(1)
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("content.json -> %s" % path)
    print("下一步：填内容 → python build.py content.json → check_layout.py → validate.py → to_pdf.py")
    return path


if __name__ == "__main__":
    main()
