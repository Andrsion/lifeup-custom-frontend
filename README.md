# 自定义人升 · 自定义界面 + AI + MCP

> 在《人升》(LifeUp) 之上构建第三方自定义界面：网页看板、桌面仪表盘、AI 助手或群机器人。人升与云人升负责真实数据和业务规则；本项目提供展示、交互与转发层。本项目不是人升 App 自带的外观设置，也不是官方仓库。

## 你想做什么？

| 目标 | 从这里开始 |
| --- | --- |
| 让 AI 帮你搭建自定义界面 | 阅读[实现方案](docs/custom-ui-ai-mcp.md)与[AI 施工标准](docs/ai-build-standard.md)，再把这两份文档交给本地运行的 AI Agent |
| 查接口方法、参数、响应与版本要求 | [API 速查表](docs/api-cheatsheet.md)，并以对应的[官方资料](llms.txt#权威来源与分工)核对 |
| 排查连接、Token、CORS 或写操作问题 | [排错指南](docs/troubleshooting.md) |
| 直接运行或改造示例 | [minimal-html](examples/minimal-html/)、[desktop-dashboard](examples/desktop-dashboard/)、[group-bot](examples/group-bot/) |
| 制作特定世界观的界面 | [主题施工稿目录](docs/specs/)；每个主题稿是设计参考，不是 API 规范 |
| 让 AI 快速理解整个仓库 | 先读 [llms.txt](llms.txt)；需要完整上下文时再读 [llms-full.txt](llms-full.txt) |

## 给 AI Agent 的启动指令

将下面的指令和本仓库的主文档交给你正在使用的 AI 工具。请优先使用能在你自己的电脑上运行代码、访问手机局域网的 Agent；云端托管环境通常无法直接访问手机上的云人升服务。

```text
我要基于本仓库搭建 LifeUp（人升）的自定义界面。请先读取：
1. llms.txt（任务路由与硬性规则）
2. docs/custom-ui-ai-mcp.md（实现方案）
3. docs/ai-build-standard.md（施工、安全与验证标准）

然后按文档中的快速上手流程检查现有项目、运行环境和配置，先进行只读连通测试，再逐步实现。接口名、参数、请求体、响应结构、权限与版本门槛必须依据对应官方资料核对，不得臆造。不得用假数据冒充真实用户数据；写操作不得自动重试；Token / API Key 不得放进前端或日志。完成后运行可用检查，并明确列出已验证与未验证的内容。

我的主题与需求：<在此填写；也可以留空>
我的运行环境：<Windows / macOS / Linux；Node.js 状态>
```

## 可运行示例

| 示例 | 用途 |
| --- | --- |
| [minimal-html](examples/minimal-html/) | 简单网页看板与本地代理 |
| [desktop-dashboard](examples/desktop-dashboard/) | 大屏仪表盘 |
| [group-bot](examples/group-bot/) | 群机器人基础示例 |

具体配置与启动步骤以各示例目录中的说明为准；不要假设所有示例都能通过双击启动或无需配置。

## 核心文档

- [实现方案](docs/custom-ui-ai-mcp.md)：项目边界、快速开始、架构、接口调用与 MCP 接入。
- [API 速查表](docs/api-cheatsheet.md)：常用 HTTP 接口、错误处理、字段与版本提示。
- [AI 施工标准](docs/ai-build-standard.md)：接口核对、安全、测试与交付检查。
- [排错指南](docs/troubleshooting.md)：连接、认证、跨域与写操作排错。
- [世界观 / 主题参考](docs/samples.md)、[从书到人升](docs/books-to-lifeup.md)、[地球 Online 梗词表](docs/earth-online-glossary.md)：玩法与内容灵感。
- [主题规格模板](docs/theme-spec-template.md) 与 [主题施工稿](docs/specs/)：将主题想法转成可实施的界面规格。

## 官方资料与版本要求

官方资料入口和冲突处理规则集中维护在 [llms.txt](llms.txt#权威来源与分工)。不同能力的版本门槛必须分别核对；不要将基础 HTTP、URL Scheme、MCP 和 Skills 的要求混为一个数字。

## 仓库维护

- 运行 `python3 scripts/build_llms.py` 可重建 `llms-full.txt`。
- 运行 `python3 scripts/check_repo.py` 可检查配置、脚本语法、本地 Markdown 链接与全文生成稳定性。
- `llms-full.txt` 是生成文件，请修改源文档或生成脚本，不要手工编辑它。

本仓库为社区整理的公开镜像版，非 LifeUp 官方仓库。接口和参数细节以官方文档为准。许可信息见 [LICENSE](LICENSE)。
