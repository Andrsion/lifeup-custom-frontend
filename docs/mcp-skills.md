# LifeUp MCP 与 Skills 指南

> 本文补充 [MCP 安装与使用指南](mcp-quickstart.md)，说明 MCP 工具和 Agent Skills 的区别、客户端差异与常见工作流。具体工具、参数、版本门槛以[官方 MCP 文档](https://wiki.lifeupapp.fun/zh-cn/guide/api_mcp.md)及[官方 SDK 当前实现](https://github.com/Ayagikei/LifeUp-SDK/tree/main/mcp)为准。

## 1. MCP 与 Skills 分别做什么？

- **MCP Server** 提供连接和可调用工具，让 AI 客户端能够发现云人升、读取数据、调用 LifeUp API。
- **Skill** 是给 Agent 的任务说明与工作流程，指导它何时读取数据、如何选择工具、调用前要查哪些参数，以及如何验证写操作结果。
- **两者配合**：MCP 提供“能做什么”的工具接口，Skill 提供“如何正确完成任务”的操作指南。

安装 MCP 不代表任意客户端都会把 Skill 作为独立文件自动加载；客户端集成方式不同，按下文选择即可。

## 2. 是否需要单独安装 Skills？

官方 SDK 将 MCP Server 与 `lifeup-cloud` Skill 一起打包在 `@lifeup/mcp` 中，没有独立的 npm Skill 包。内置文档可通过 MCP 的 `help` 工具读取。

| 客户端 / Agent 类型 | 推荐方式 | 注意事项 |
| --- | --- | --- |
| Cursor、Claude Desktop、WorkBuddy 等通过 MCP 使用的客户端 | 先安装 MCP，再通过工具 `help` 读取内置指引 | 不要再安装一份重复 Skill；具体客户端是否支持独立 Skill 取决于其能力 |
| Claude Code、Pi、支持 Skill 目录的 Agent | 安装 MCP，并按 Agent 的 Skill 机制指向或复制官方 `mcp/skills/lifeup-cloud/` | 若复制到本地，更新时需自行同步官方版本 |
| 自定义 Agent / 其他客户端 | 先确认它支持 MCP；若支持 Skill，再分别配置 MCP 连接和 Skill 文件 | 不要假定仅添加 MCP 配置就会自动读取本地 Skill |

官方参考：
- [官方 MCP 包说明](https://github.com/Ayagikei/LifeUp-SDK/blob/main/mcp/README.md)
- [官方 Skill 目录](https://github.com/Ayagikei/LifeUp-SDK/tree/main/mcp/skills/lifeup-cloud)
- [官方 MCP & Skills Wiki](https://wiki.lifeupapp.fun/zh-cn/guide/api_mcp.md)

## 3. 安装和更新

### 方案 A：使用 npm（推荐）

在 MCP 客户端配置中添加以下条目。应合并进现有配置，不要覆盖其他 MCP 服务：

```json
{
  "mcpServers": {
    "lifeup": {
      "command": "npx",
      "args": ["-y", "@lifeup/mcp"]
    }
  }
}
```

包中已包含工具和 Skill 指引，不需要另找所谓独立的 Skill npm 包。配置修改后按客户端要求重新加载或重启。

### 方案 B：从官方仓库安装

官方 SDK 提供安装脚本，可构建 MCP 并更新检测到的客户端配置：

```bash
git clone https://github.com/Ayagikei/LifeUp-SDK.git
cd LifeUp-SDK
./scripts/install-mcp.sh
```

安装脚本的客户端覆盖范围取决于当前版本与本机配置。运行前先阅读官方 [mcp/README.md](https://github.com/Ayagikei/LifeUp-SDK/blob/main/mcp/README.md)，检查脚本将修改哪些配置；不要盲目覆盖已有设置。

如果图形客户端找不到 `npx`，可按官方 README 使用 `npx` / `node` 绝对路径，或本地构建后直接运行 MCP 的入口文件。

### 独立配置 Skill

仅在 Agent 支持独立 Skill 路径时才需要。使用官方文件夹 `mcp/skills/lifeup-cloud/`，而不是只复制一个孤立的 `SKILL.md`；其下可能包含参考资料。可按 Agent 的规则引用该目录，或复制到 Agent 的 Skill 目录。

若需要定制工作流程，建议复制到自己的项目中再修改，并保留官方文档链接；不要直接改写接口事实、版本要求或工具参数而不核对来源。

## 4. 连接和工具调用的推荐流程

1. **`discover`**：尝试通过 mDNS 发现云人升；只有一个实例时通常可以自动连接。
2. **`connect`**：没有发现或发现多个实例时，按工具要求指定实际的主机地址；只有云人升启用了 Token 才提供 Token。
3. **`status`**：检查连接状态与版本。当前 Skill 的完整工作流要求人升 1.106.0+、云人升 3.0.1+；这不是所有 Cloud HTTP 路由的统一门槛。
4. **只读读取**：优先用 `list_data` 或对应的列表工具，按类别读取所需数据；若有类别 ID，优先使用类别筛选，避免无必要地读取全部数据。
5. **查具体 API**：先用 `help api-index` 查看方法索引，再用 `help <method>` 获取当前要调用方法的参数说明。不要把整份 API 索引全部塞进上下文。
6. **执行写操作**：先匹配唯一目标并展示执行计划；对于删除、修改金币、导出备份、历史操作等破坏性操作，严格遵循当前工具要求的确认参数。
7. **核对结果**：读取工具返回的 `calls[].ok`、`calls[].data` 等实际结果，必要时重新读取对应数据；超时或结果不明时不要直接重放写请求。

常用任务与工具（名称以当前已安装版本实际暴露的工具为准）：

| 目标 | 常见工具 / 路径 |
| --- | --- |
| 读取任务和其他数据 | `list_data`、`list_tasks`、`list_items` 等 |
| 完成任务 | `complete_task`；重复任务优先使用稳定的 `gid` 或准确名称，不要盲目沿用可能变化的实例 ID |
| 新建任务 | `add_task` |
| 查询金币 / 基本信息 | `get_coin`、`get_info` |
| 发放奖励 / 购买商品 | `reward`、`purchase_item` |
| 调用其他 API | `call_api`；需要多个 API 时按官方说明考虑 `call_api_batch` |
| 查看事件能力 | 通过 `help broadcasts` 查阅当前支持的事件工具 |

如果客户端里没有列出这些工具，先让 Agent 输出实际可用工具和版本，不要假设每个版本都完全一致。

## 5. 事件和自动化（进阶）

官方 SDK 还提供事件相关能力。若需要基于任务完成或奖励等广播做自动化：

- 按官方说明在人升中启用“实验 → 广播事件”（菜单名称可能随版本变化）。
- 先通过 MCP 的 `help broadcasts` 查看当前事件说明，再检查实际可用的事件列表或订阅工具。
- 事件订阅与 HTTP 查询是不同能力；不要把事件未到达直接判断为任务写入失败。
- 自动化触发写操作时仍要做目标校验、权限检查和结果核验，避免重复奖励、重复创建等副作用。

事件端点、事件类型和订阅参数会随实现变化，请以[官方 SDK 当前 MCP 实现](https://github.com/Ayagikei/LifeUp-SDK/tree/main/mcp)和[云人升 HTTP 文档](https://wiki.lifeupapp.fun/zh-cn/guide/api_cloud.md)为准。

## 6. 版本、权限与凭据

- **当前 Skill 工作流**：人升 1.106.0+、云人升 3.0.1+。官方 Wiki MCP 页面可能仍写云人升 3.0.0+；需要完整当前 Skill 工作流时，采用更具体的 Skill 要求。
- **读取权限**：在云人升授予“读取人升数据”权限；未授权时，连接成功也可能读不到数据。
- **Token**：只有云人升配置了 API Token 时才提供；使用原始 Token，不加 `Bearer ` 前缀。不要提交到仓库、URL、前端、日志或公开聊天。
- **网络**：手机和运行 MCP 的电脑通常需要在同一局域网；自动发现失败时按官方文档设置实际的 `LIFEUP_HOST`。
- **权限最小化**：先使用只读查询验证连通性，再执行写操作。不要把 MCP 的可调用能力理解成所有操作都应自动执行。

## 7. 排错顺序

1. 先确认云人升服务正在运行，手机和电脑可以互访。
2. 确认客户端实际加载了名为 `lifeup` 的 MCP Server，必要时重启客户端。
3. 让 Agent 列出当前工具并调用只读的 `status` / 数据查询。
4. 若自动发现失败，核对 IP、端口和 `LIFEUP_HOST`；若认证失败，检查 Token 是否真的启用且格式正确。
5. 若工具存在但 Agent 不按预期执行，确认客户端是否需要单独配置 Skill；支持内置 `help` 的客户端先读取对应指引。
6. 仍无法解决时，收集错误信息和版本号，但先删除 Token、IP 等不宜公开的敏感信息，再查看[官方 MCP 文档](https://wiki.lifeupapp.fun/zh-cn/guide/api_mcp.md)及[官方 SDK](https://github.com/Ayagikei/LifeUp-SDK)。

## 8. 延伸阅读

- [MCP 安装与使用指南](mcp-quickstart.md) — 安装、首次连接与基础用法。
- [官方 MCP & Skills Wiki](https://wiki.lifeupapp.fun/zh-cn/guide/api_mcp.md) — 官方接入流程。
- [官方 MCP 包 README](https://github.com/Ayagikei/LifeUp-SDK/blob/main/mcp/README.md) — 安装方式、客户端差异与环境变量。
- [官方 Skill 源码](https://github.com/Ayagikei/LifeUp-SDK/tree/main/mcp/skills/lifeup-cloud) — 当前工作流、工具使用与版本要求。
- [官方云人升 HTTP API](https://wiki.lifeupapp.fun/zh-cn/guide/api_cloud.md) — HTTP 接口、权限与事件能力。
