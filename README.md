# 自定义人升 · 自定义界面 + AI + MCP

在《人升》(LifeUp) 与云人升之上构建网页看板、桌面仪表盘、AI 助手或群机器人。本项目是第三方展示与交互层，不是人升官方仓库，也不替代 App 内的业务规则。

## 先选一条路

| 你的目标 | 从这里开始 |
| --- | --- |
| **我想直接运行示例** | 进入 [minimal-html](examples/minimal-html/)，按示例说明配置并启动；需要大屏时用 [desktop-dashboard](examples/desktop-dashboard/)。 |
| **我想让 AI 帮我做** | 先读 [llms.txt](llms.txt)，再按任务读取 [实现方案](docs/custom-ui-ai-mcp.md) 和 [AI 施工标准](docs/ai-build-standard.md)。群机器人示例见 [group-bot](examples/group-bot/)。 |
| **我只想用 AI 操作人升（MCP）** | 按 [MCP 安装与使用指南](docs/mcp-quickstart.md) 配置客户端，不需要自己开发界面。 |
| **我遇到问题了** | 先运行下面的只读诊断，再查 [排错指南](docs/troubleshooting.md)；接口细节见 [API 速查表](docs/api-cheatsheet.md)。 |

## 开工前 5 分钟自检

1. **确认手机侧版本与权限**：基础 Cloud HTTP 查询的官方要求是人升 v1.91+ 与最新版云人升；部分字段或能力需要更高版本。MCP / Skills 的版本要求不同，见下方说明。
2. **确认网络**：手机与电脑通常需要在同一局域网；确认云人升显示的 IP 和端口，默认端口为 `13276`。
3. **确认运行环境**：本地示例需要 Node.js 20+。Trae、通义灵码、CodeBuddy、Cursor、Claude Code 等均可考虑，关键是 Agent 能在本机读写项目、执行命令，并访问手机所在的局域网；纯云端托管环境通常做不到。
4. **准备本地配置**：进入要运行的示例目录，将 `config.example.json` 复制为 `config.json`，按示例说明填写云人升地址。不要提交真实配置或 Token。
5. **执行只读诊断**：在仓库根目录运行：

   ```bash
   node scripts/doctor.js examples/minimal-html
   ```

   若检查失败，先按输出检查配置、网络和官方文档；不要用写操作来测试连通性。若检查其他示例，将参数替换为相应目录，例如 `examples/desktop-dashboard`。诊断工具只读取 `GET /info`，不会完成任务、购买或发放奖励。

## 给 AI Agent 的启动指令

将下面的指令和仓库交给你使用的本地 AI Agent。项目文档以 GitHub 仓库 `main` 分支当前内容为准；若通过镜像读取，先确认镜像同步情况。接口事实以对应官方资料为准。

```text
请先读取仓库根目录的 llms.txt，并按任务路由继续读取 docs/ai-build-standard.md、docs/custom-ui-ai-mcp.md 及相关示例。先盘点现有文件与运行环境，再做最小必要修改。

接口路径、方法、参数、请求体、响应字段、权限与版本门槛必须核对对应官方资料，不得臆造。先做只读连通测试，不得用假数据冒充真实用户数据。Token / API Key 不得进入前端、URL、公开仓库或日志。写操作必须由用户明确触发，检查业务级结果；超时或结果不明时不得自动重试。

完成后运行可用的检查和测试，并列出实际执行的命令、通过 / 失败结果、真实设备联调情况及未验证事项。不要声称运行过未实际执行的测试。
我的主题与需求：<可选填写>
我的运行环境：<Windows / macOS / Linux；Node.js 版本；所用本地 Agent>
```

## 直接让 AI 操作人升（MCP）

如果你不需要自定义网页，只想让 AI 查询任务、分析数据或按你的指令操作人升，请从 [MCP 安装与使用指南](docs/mcp-quickstart.md) 开始。指南包含环境准备、客户端配置、首次连接验证、常见提问和安全注意事项。

## 版本门槛：按能力分别核对

| 能力 | 当前文档口径 |
| --- | --- |
| Cloud HTTP 基础查询 | 官方 Cloud HTTP 文档要求人升 v1.91+ 与最新版云人升；具体路由、字段和权限仍以对应文档为准。 |
| HTTP 特定字段 / 能力 | 逐项核对版本要求。例如 `weekdays` 标注人升 v1.106.0+；这不是所有 HTTP 路由的统一门槛。 |
| URL Scheme | 方法名、参数与个别方法的版本要求以[官方 API 文档](https://wiki.lifeupapp.fun/zh-cn/guide/api.md)对应条目为准，不把它与 HTTP 版本要求混用。 |
| MCP 接入 | 按[官方 MCP 文档](https://wiki.lifeupapp.fun/zh-cn/guide/api_mcp.md)检查客户端接入要求；该 Wiki 页面目前写云人升 3.0.0+。 |
| 当前 Skills 工作流 | 当前官方 `lifeup-cloud` Skill 要求人升 v1.106.0+、云人升 3.0.1+。如需完整当前 Skills 工作流，按更具体的 Skill 要求使用 3.0.1+；这不是所有 HTTP 路由的统一门槛。 |

权威资料入口和冲突处理规则见 [llms.txt](llms.txt#权威来源与分工)。若官方文档提示定义可能滞后，再核对它指向的官方 SDK 实现；无法确认时应明确标注不确定，不得猜测。

## 仓库维护

- `node scripts/doctor.js <示例目录>`：检查本地配置并只读请求 `GET /info`，例如 `node scripts/doctor.js examples/minimal-html`。
- `node scripts/test_proxy.js`：运行本地代理集成测试，使用 mock 上游，不会访问真实手机。
- `python3 scripts/check_repo.py`：检查配置、脚本语法、本地 Markdown 链接和 `llms-full.txt` 生成稳定性。
- `llms-full.txt` 是生成文件；修改源文档后由 `scripts/build_llms.py` 重建，不要手工编辑。

本仓库为社区整理的公开项目，非 LifeUp 官方仓库。许可信息见 [LICENSE](LICENSE)。
