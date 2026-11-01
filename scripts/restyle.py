# -*- coding: utf-8 -*-
"""换配色（原地改属性，不重新渲染正文）

用法：
  python restyle.py <html> --theme T2 [--pdf]

为什么只换配色：配色是纯 CSS 变量，改 data-theme 即可；
版式（L1/L2/L3）决定「保留哪些段落」，是在 build.py 里筛的，
只能从 content.json 重新 build —— 本脚本检测到 --layout 会直接拒绝并给出正确命令。
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import config  # noqa: E402

THEMES = {"T0": "深蓝橙", "T1": "商务蓝", "T2": "深色科技", "T3": "公文墨"}


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        raise SystemExit(1)

    if "--layout" in args:
        config.out("版式不能原地切换：版式决定保留哪些段落，需从 content.json 重新生成。\n"
                   "请改用：python scripts/build.py content.json --layout %s --theme <配色>"
                   % args[args.index("--layout") + 1].upper())
        raise SystemExit(2)

    src_path = os.path.abspath(args[0])
    html = open(src_path, encoding="utf-8").read()
    cur = (re.search(r'data-theme="([^"]*)"', html) or [None, "T0"])[1]
    theme = cur
    for i, a in enumerate(args):
        if a == "--theme" and i + 1 < len(args):
            theme = args[i + 1].upper()
    if theme not in THEMES:
        raise SystemExit("未知配色 %s，可选 %s" % (theme, "/".join(THEMES)))
    if theme == cur:
        config.out("配色未变化（已是 %s/%s）" % (theme, THEMES[theme]))
        return src_path

    html = re.sub(r'(<html[^>]*?)data-theme="[^"]*"',
                  r'\1data-theme="%s"' % theme, html, count=1)

    layout = (re.search(r'data-layout="([^"]*)"', html) or [None, "L1"])[1]
    stem = os.path.splitext(src_path)[0]
    m = re.match(r"^(.*?)-L[123](-T[0-3])?-[^-]+$", stem)
    base = m.group(1) if m else stem
    dst = "%s-%s-%s-%s.html" % (base, layout, theme, THEMES[theme])
    open(dst, "w", encoding="utf-8").write(html)
    config.out("HTML -> %s  配色=%s(%s)" % (dst, theme, THEMES[theme]))

    if "--pdf" in args:
        r = subprocess.run([sys.executable, os.path.join(HERE, "to_pdf.py"), dst],
                           capture_output=True)
        config.out(r.stdout.decode("utf-8", "replace").strip())
        if r.returncode != 0:
            raise SystemExit(1)
    return dst


if __name__ == "__main__":
    main()
