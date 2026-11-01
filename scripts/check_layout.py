# -*- coding: utf-8 -*-
"""A4 分页体检：溢出 + 填充率

用法：
  python check_layout.py <html> [--min-fill 62] [--json]

判读：
  OVERFLOW>0  内容被 overflow:hidden 裁掉 —— 必须移动整块或收紧行距
  OVERFLOW=0  合格
  FILL<min    页面过空 —— 补内容或换小版式（单页精要 / 双页标准）
退出码：0 合格；1 有溢出；2 无溢出但页面过空或缺测量结果。
"""
import json
import os
import pathlib
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import config  # noqa: E402

PROBE = """
<script>
window.addEventListener('load', function () {
  var out = [], lines = [];
  document.querySelectorAll('.page').forEach(function (p, i) {
    var cs = getComputedStyle(p);
    var ptop = parseFloat(cs.paddingTop), pbot = parseFloat(cs.paddingBottom);
    var box = p.getBoundingClientRect();
    var inner = p.clientHeight - ptop - pbot;
    var top = box.top + ptop;
    var bottom = top, cbottom = top, secs = [];
    Array.prototype.forEach.call(p.children, function (c) {
      var r = c.getBoundingClientRect();
      secs.push((c.className || c.tagName) + '=' + Math.round(r.height));
      if (r.bottom > bottom) bottom = r.bottom;
      var isTail = /(^|\\s)(note|footer)(\\s|$)/.test(c.className || '') ||
                   c.tagName === 'FOOTER';
      if (!isTail && r.bottom > cbottom) cbottom = r.bottom;
    });
    var fill = inner > 0 ? ((bottom - top) / inner * 100) : 0;
    var cfill = inner > 0 ? ((cbottom - top) / inner * 100) : 0;
    var ov = p.scrollHeight - p.clientHeight;
    lines.push({page: i + 1, overflow: ov, fill: Math.round(fill * 10) / 10,
                cfill: Math.round(cfill * 10) / 10,
                scrollH: p.scrollHeight, clientH: p.clientHeight, blocks: secs});
    out.push('PAGE' + (i + 1) + ' OVERFLOW=' + ov +
             ' CFILL=' + cfill.toFixed(1) + '%' +
             ' H=' + p.scrollHeight + '/' + p.clientHeight +
             ' :: ' + secs.join(', '));
  });
  var d = document.createElement('div');
  d.id = 'jb-probe';
  d.textContent = JSON.stringify(lines);
  d.setAttribute('data-lines', out.join(' ## '));
  document.body.appendChild(d);
});
</script>
</body>"""


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        raise SystemExit(1)
    html = os.path.abspath(args[0])
    min_fill = 62.0
    if "--min-fill" in args:
        min_fill = float(args[args.index("--min-fill") + 1])

    tmp = config.tmp_dir("jb-probe")
    probe_path = os.path.join(tmp, "_probe.html")
    src = open(html, encoding="utf-8").read()
    open(probe_path, "w", encoding="utf-8").write(src.replace("</body>", PROBE))

    prof = config.profile_dir()
    cmd = [config.browser(), "--headless=new", "--disable-gpu", "--no-sandbox",
           "--virtual-time-budget=6000", "--dump-dom",
           "--user-data-dir=" + prof, pathlib.Path(probe_path).as_uri()]
    p = config.run(cmd, timeout=120)
    dom = p.stdout.decode("utf-8", errors="replace")

    m = re.search(r'id="jb-probe"[^>]*>(.*?)</div>', dom, re.S)
    if not m:
        config.out("PROBE_NOT_FOUND：页面未渲染出测量结果（检查 HTML 是否完整）")
        raise SystemExit(2)
    raw = m.group(1).replace("&quot;", '"')
    try:
        pages = json.loads(raw)
    except Exception:
        config.out("测量结果解析失败：%s" % raw[:300])
        raise SystemExit(2)

    name = os.path.basename(html)
    worst = 0
    low = []
    for pg in pages:
        flag = "OVF" if pg["overflow"] > 0 else ("LOW" if pg["cfill"] < min_fill else "OK ")
        config.out("%s %s P%d  overflow=%d cfill=%.1f%%  %s"
                   % (flag, name, pg["page"], pg["overflow"], pg["cfill"],
                      " / ".join(pg["blocks"])[:120]))
        if pg["overflow"] > worst:
            worst = pg["overflow"]
        if pg["cfill"] < min_fill:
            low.append(pg["page"])

    config.out("---- 页数=%d 最大溢出=%dpx 内容填充率低于 %.0f%% 的页=%s"
               % (len(pages), worst, min_fill, low or "无"))

    if "--json" in args:
        json.dump(pages, open(os.path.join(os.path.dirname(html), "layout.json"),
                              "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    shutil.rmtree(tmp, ignore_errors=True)
    if worst > 0:
        raise SystemExit(1)
    if low:
        raise SystemExit(2)
    return 0


if __name__ == "__main__":
    main()
