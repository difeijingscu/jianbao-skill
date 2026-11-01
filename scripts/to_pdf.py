# -*- coding: utf-8 -*-
"""HTML -> A4 PDF（Chrome/Edge headless 打印）

用法：
  python to_pdf.py <html> [pdf]

要点：
  --no-pdf-header-footer 必须带，否则浏览器会加自己的页眉页脚。
  打印后回读页数做校验，页数为 0 视为失败。
"""
import os
import pathlib
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import config  # noqa: E402


def count_pages(pdf):
    try:
        from pypdf import PdfReader  # 有则用，最稳
        return len(PdfReader(pdf).pages)
    except Exception:
        pass
    raw = open(pdf, "rb").read()
    n = len(re.findall(rb"/Type\s*/Page(?![s])", raw))
    return n


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        raise SystemExit(1)
    html = os.path.abspath(args[0])
    pdf = os.path.abspath(args[1]) if len(args) > 1 else os.path.splitext(html)[0] + ".pdf"
    if os.path.exists(pdf):
        os.remove(pdf)

    cmd = [config.browser(), "--headless=new", "--disable-gpu", "--no-sandbox",
           "--no-pdf-header-footer", "--run-all-compositor-stages-before-draw",
           "--virtual-time-budget=8000",
           "--user-data-dir=" + config.profile_dir(),
           "--print-to-pdf=" + pdf, pathlib.Path(html).as_uri()]
    p = config.run(cmd, timeout=240)

    if not os.path.exists(pdf):
        config.out("PDF 生成失败 rc=%s\n%s"
                   % (p.returncode, p.stderr.decode("utf-8", "replace")[:400]))
        raise SystemExit(1)
    n = count_pages(pdf)
    config.out("PDF -> %s  size=%.1fKB  pages=%d" % (pdf, os.path.getsize(pdf) / 1024.0, n))
    if n == 0:
        config.out("页数解析为 0，PDF 可能损坏")
        raise SystemExit(1)
    return pdf


if __name__ == "__main__":
    main()
