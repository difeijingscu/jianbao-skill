# -*- coding: utf-8 -*-
"""公共环境探测：浏览器、Chrome 用户目录、子进程调用。

所有绝对路径集中在这里，换机只需改本文件或设环境变量：
  JB_BROWSER  浏览器可执行文件路径
  JB_TMP      临时目录（默认系统 temp）
"""
import os
import shutil
import subprocess
import sys
import tempfile

_BROWSER_CANDIDATES = [
    # Windows
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    # macOS
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    # Linux
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/snap/bin/chromium",
]


def browser():
    """返回可用的 Chromium 内核浏览器路径（Windows / macOS / Linux 自动探测）。

    找不到则抛异常并给出可操作提示。
    """
    env = os.environ.get("JB_BROWSER")
    if env and os.path.exists(env):
        return env
    for p in _BROWSER_CANDIDATES:
        if os.path.exists(p):
            return p
    for name in ("chrome", "chromium", "google-chrome", "msedge"):
        p = shutil.which(name)
        if p:
            return p
    raise RuntimeError(
        "未找到 Chrome/Edge。安装 Chrome，或设置环境变量 JB_BROWSER 指向可执行文件。")


def tmp_dir(tag="jb"):
    """每次运行独立临时目录，避免多任务共用 user-data-dir 互相上锁。"""
    base = os.environ.get("JB_TMP") or tempfile.gettempdir()
    d = os.path.join(base, "%s-%d" % (tag, os.getpid()))
    os.makedirs(d, exist_ok=True)
    return d


def profile_dir():
    """浏览器 profile 目录。放在临时目录，不污染交付目录。"""
    d = os.path.join(tmp_dir("jb-profile"), "profile")
    os.makedirs(d, exist_ok=True)
    return d


def run(cmd, timeout=180):
    p = subprocess.run(cmd, capture_output=True, timeout=timeout)
    return p


def out(text):
    """统一输出：Windows 控制台默认 GBK，强制 utf-8 写，失败则降级。"""
    try:
        sys.stdout.buffer.write((text + "\n").encode("utf-8"))
        sys.stdout.flush()
    except Exception:
        print(text)


def skill_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
