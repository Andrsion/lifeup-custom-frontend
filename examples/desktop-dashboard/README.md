# 大屏看板（桌面 / 平板常驻）

同一个「三层架构」，但布局是为**大屏**优化：多列任务卡片、大字号、右上角时钟、**每 15 秒自动刷新**。
适合挂在平板、副屏、电视上，当「今日任务墙」。

```
index.html   ← 大屏前端
proxy.js     ← 与 minimal-html 相同（本地代理）
config.json  ← 你的手机 IP
start.bat / start.command
```

## 跑起来

和 [minimal-html](../minimal-html/) 完全一样：

1. 手机：按官方云人升 HTTP 文档准备人升 v1.91+ 与最新版云人升，并开「读取人升数据」；特定字段 / 功能可能需要更高版本，先请求 `/info` 并核对官方文档。
2. 电脑：Node.js **20+**；与手机同一 Wi‑Fi。
3. 复制 `config.example.json` 为 `config.json`，改 `host` 为 `IP:13276`。
4. 双击 `start.bat` / `start.command`（或 `node proxy.js`）。
5. 打开 **http://127.0.0.1:8787**，按 `F11` 全屏。
6. 排错可运行 `node scripts/doctor.js examples/desktop-dashboard`（在仓库根目录执行）；它只读检查官方文档列出的 `/info`。

## 想更"游戏化"？

- 把 `UI.coin` 改成你的货币叫法（铃钱 / 灵石 / 丁尼…），背景色改成主题色。
- 需要整屏皮肤、立绘、进度条，就把 [实现方案](../../docs/custom-ui-ai-mcp.md) 丢给本地 AI 工具，让它在这份样板基础上改。

## 顶栏直接改地址（不用打开 config.json）

页面顶部有地址框，填云人升首页显示的 `IP:13276` 后点「换」即刻生效。
**这是临时切换，不写入 `config.json`**——重启后回到配置文件里的地址；要长期生效请改 `config.json` 的 `host`。

## 安全说明

- 本地代理默认只监听回环地址，不开放局域网访问；Token 保存在本地代理配置中。
- 不要把真实的 `config.json` 提交到仓库。

## 提醒

- 桌面浏览器建议用 Chrome / Edge / Safari 最新版。
- 大屏常驻时，可把 `load()` 的自动刷新间隔从 15000ms 调长一点，省电。
