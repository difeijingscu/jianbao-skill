# 环境要求与已知问题

## 依赖

- **Python 3.8+**，只用标准库，无需 `pip install`。
- **Chromium 内核浏览器**：Chrome / Chromium / Edge 任一，用于「版面体检」与「导出 PDF」。
  脚本按以下顺序自动探测，找不到才报错：

  1. 环境变量 `JB_BROWSER`
  2. 各平台默认安装路径（Windows 的 Program Files、macOS 的 `/Applications`、Linux 的 `google-chrome`）
  3. `PATH` 里的 `chrome` / `chromium` / `google-chrome` / `msedge`

  自定义安装位置时：

  ```bash
  export JB_BROWSER="/opt/google/chrome/chrome"      # Linux / macOS
  set JB_BROWSER="D:\Apps\Chrome\chrome.exe"          # Windows
  ```

- **中文字体**：版式按「思源黑体 / PingFang / 微软雅黑」的回退链设计。Linux 容器若缺中文字体，
  渲染会变方框，装一个即可：`apt-get install fonts-noto-cjk`。

## 已知问题

### 1. 内容被静默裁掉，日志却一切正常

`.page` 固定 `height: 297mm` 且 `overflow: hidden`——A4 尺寸是硬约束，超出部分**不会报错，直接消失**。
这是必须跑 `check_layout.py` 的唯一原因。改完内容不体检就交付，是最常见的翻车方式。

### 2. 填充率过低被误判为合格

只查溢出会让「一页只填 60%」的稿子通过。`check_layout.py` 同时输出填充率，低于阈值会列出页码。
处理顺序：**先补有信息量的内容**，其次换小版式（L2），最后才动边距——不要靠拉大间距把版面撑满。

### 3. PDF 多出浏览器自带的页眉页脚

必须带 `--no-pdf-header-footer`。`to_pdf.py` 已处理，手写命令时容易漏。

### 4. 浏览器 profile 目录污染交付目录

`--user-data-dir` 必须指向临时目录（`config.profile_dir()` 已如此）。
放进工作目录会残留 `_chrome_prof/`，且多个任务共用一个目录会互相上锁、随机失败。

### 5. Windows 控制台中文乱码

`sys.stdout` 默认 GBK，直接 `print` 中文在重定向到文件时会乱码。
`config.out()` 统一用 `sys.stdout.buffer` 写 UTF-8。新脚本也要走这个函数，不要直接 `print`。

### 6. Windows 上找不到 `pypdf`

`to_pdf.py` 用 `pypdf` 数页，没有则回退正则匹配 `/Type /Page`。
两者都不可用时该步视为失败，但不影响 HTML 产出——**页数以 `check_layout.py` 的输出为准**。

### 7. 文件名里的主题被压扁

`slug()` 只保留字母、数字、CJK，其余字符转连字符并压缩重复。
如 `Super-agent` → `Superagent`。这是有意的（避免文件名里出现空格与特殊符号），不是 bug。
需要精确控制文件名时用 `build.py -o` 指定。

## 打印尺寸基准

A4 @96dpi：`210mm = 794px`，`297mm = 1123px`。
`check_layout.py` 的浏览器窗口按这个尺寸设置，改窗口尺寸会让填充率读数失真。
