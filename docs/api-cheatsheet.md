# 云人升 HTTP 接口 · 速查表

> ⚠️ 本表仅供**速查 / 防臆造**，并以官方资料交叉核对：HTTP 路由、权限与基础版本要求以 [官方云人升 HTTP 文档](https://wiki.lifeupapp.fun/zh-cn/guide/api_cloud.md) 为入口；`lifeup://api/...` 方法名与参数以 [官方 URL Scheme / API 文档](https://wiki.lifeupapp.fun/zh-cn/guide/api.md) 为准。
>
> **来源分工与冲突处理**：官方 Wiki 是首要文档依据；`api_cloud.md` 提示部分接口定义可能滞后，因此仅在 HTTP 路由、参数或响应与文档不一致时，再核对它指向的 [官方 SDK HTTP 服务端实现](https://github.com/Ayagikei/LifeUp-SDK/blob/main/http/src/main/java/net/lifeupapp/lifeup/http/service/KtorService.kt)。MCP 安装与客户端接入看 [官方 MCP 文档](https://wiki.lifeupapp.fun/zh-cn/guide/api_mcp.md)；当前 Skills 的具体能力和版本要求看 [官方 `lifeup-cloud` Skill](https://github.com/Ayagikei/LifeUp-SDK/tree/main/mcp/skills/lifeup-cloud)。不同资料有冲突时，应明确标注冲突，不要把 MCP / Skills 的门槛套用到全部 HTTP 接口。
>
> 本次核对日期：2026-10-17。所核对的 SDK HTTP 服务端提交：`ab130079d7d44d1694f96481fa732148860d0b39`。地址形如 `http://<手机IP>:13276`（局域网）。
>
> 基础 HTTP 查询的前置条件、权限和版本要求按官方云人升 HTTP 文档确认；特定字段 / 功能另有门槛。MCP / Skills 版本要求与基础 HTTP 不同，见下方版本说明。

## 0. 基础

- 主机：`http://{手机IP}:13276`（默认端口 **13276**，以云人升显示为准）
- 统一响应：`{ code, message, data }`。**`code=200` 只表示传输成功**
  - JSON `code=10001`：人升未运行 / 未授「读取数据」
  - JSON `code=10002`：ContentProvider 查询失败
- Token 认证失败属于 HTTP 认证层：仅当云人升配置了 Token 时适用；检查当前云人升设置与请求认证方式。HTTP 状态码和 JSON `code` 是不同层次，不把未由官方文档明确保证的状态码当作稳定业务码。
- 常见列表接口的 `data` 是**数组**；`/coin`、`/info`、`/events`、`/statistics` 返回对象结构（其中 `/events` 的事件列表位于对象内部）。`/files/{url}` 返回文件流，不套用 JSON 响应包装
- 当前官方 SDK 默认值：`/history`、`/feelings`、五种 `*_records` 接口均为 `offset=0`、`limit=100`；`/events` 为 `after=0`、`limit=50`。这些默认值是核对时 SDK 的实现，不保证旧版完全一致。
- 时间范围参数 `time_range_start` 与 `time_range_end` 是 Unix 时间戳毫秒，必须成对传入，且结束时间大于起始时间；缺失一项或区间非法可能返回 `invalid_parameter`。
- 查询数据需先在云人升申请「读取人升数据」权限。官方文档列出的基础要求为人升 v1.91+ 与最新版云人升；特定字段 / 功能有单独版本要求，不能将单个功能的版本门槛套用到全部接口。

## 1. 读（GET，需先开「读取人升数据」）

**任务**

```
GET /tasks
GET /tasks/{清单id}
GET /tasks_categories
GET /history?offset=&limit=&gid=
```

**商品 / 仓库**

```
GET /items
GET /items?id=1&id=4
GET /items/{清单id}
GET /items_categories[?include_hidden=true]
```

**成就**

```
GET /achievements
GET /achievements/{清单id}
GET /achievement_categories
GET /achievement_conditions/{成就id}
```

**感想 / 合成 / 属性**

```
GET /feelings?offset=0&limit=100
GET /synthesis
GET /synthesis/{清单id}
GET /synthesis_categories[?include_hidden=true]
GET /synthesis_categories/{清单ID}
GET /skills
GET /skill_groups[?include_hidden=true]
```

**其它**

```
GET /coin                     ← 金币余额（data 是对象）
GET /info                     ← 人升 / 云人升版本（连通自测用；data 是对象）
GET /pomodoro_records?offset=&limit=&time_range_start=&time_range_end=
GET /coin_records?offset=&limit=&time_range_start=&time_range_end=
GET /inventory_records?offset=&limit=&time_range_start=&time_range_end=
GET /exp_records?offset=&limit=&time_range_start=&time_range_end=
GET /step_records?offset=&limit=&time_range_start=&time_range_end=
GET /level_defines
GET /statistics?time_range_start=&time_range_end=
GET /events?after=0&limit=50   ← 广播事件（GET 轮询）
ws://{host}/events?after={id} ← 广播事件（WebSocket 推送）
```

**图片**

```
GET /files/{url}
```

### 进阶文件 / 备份路由（当前 SDK 实现；旧版不保证具备）

```http
GET /data/export?withMedia=true
POST /data/import
POST /files/upload
```

- `/data/export` 当前 SDK 默认 `withMedia=true`，返回备份数据响应。
- `/data/import` 使用 multipart 上传备份，并交由人升打开导入流程。
- `/files/upload` 使用 multipart 上传文件并返回 URI。
- 这些不是普通只读看板的必需接口；导入 / 上传会触发文件处理或应用流程。只有明确需要且已核对当前官方实现时才使用，不要在自动化测试中对真实账户执行导入。

## 2. 分页、权限与版本注意事项

- `/history`：`offset` / `limit` 分页，`gid` 可选，用于筛选某个重复任务组的历史记录；当前官方 SDK 默认 `0` / `100`。
- `/feelings`：分页，当前官方 SDK 默认 `offset=0`、`limit=100`。
- `/pomodoro_records`、`/coin_records`、`/inventory_records`、`/exp_records`、`/step_records`：分页默认 `offset=0`、`limit=100`；可选时间范围参数必须成对传入。
- `/statistics`：只支持可选时间范围，不使用 `offset` / `limit` 分页。
- `/events`：当前 SDK 默认 `after=0`、`limit=50`；事件数据是否产生取决于人升「广播事件」设置，WebSocket 推送另受云人升开关控制。
- 不要擅自给 `/tasks`、`/items`、`/skills` 等接口加分页参数；以各接口官方定义为准。
- 官方云人升文档标注部分接口定义可能滞后；本表的默认值以核对时的官方 SDK `KtorService.kt` 为准，旧版云人升可能不同。
- 版本：基础 HTTP 查询的官方文档要求为人升 v1.91+ 与最新版云人升；`weekdays` 字段标注人升 v1.106.0+，技能 ContentProvider 查询标注 v1.103.0+。MCP / Skills 是另一套能力：官方 Wiki 的 [MCP 文档](https://wiki.lifeupapp.fun/zh-cn/guide/api_mcp.md)目前写云人升 3.0.0+，而当前官方 SDK 的 `lifeup-cloud` Skill 要求人升 v1.106.0+、云人升 3.0.1+；如需当前完整 Skills 工作流，按更具体的 Skill 要求使用 3.0.1+，不要把它当成所有 HTTP 路由的统一最低版本。使用前可通过 `/info` 核对当前版本。

## 3. 写（调用 `lifeup://api/…`）

推荐走 **content provider 机制**（兼容性更好）：

```
# GET 形式（url 需 URL 编码；支持多个 url 参数）
GET  http://{host}:{port}/api/contentprovider?url={ENCODED}

# POST 形式（body 用 urls 数组，不需要转义）
POST http://{host}:{port}/api/contentprovider
     { "urls": ["lifeup://api/complete?id=123"] }
```

start activity 机制（部分设备会限制后台弹界面，可能失败）：

```
GET  http://{host}:{port}/api?url={ENCODED}
POST http://{host}:{port}/api
     { "urls": ["lifeup://api/goto?page=lab"] }
```

> ⚠️ **写操作不幂等**：`complete` / `give_up` / `reward` 等超时后**不要自动重试**。
> ⚠️ `/api/contentprovider` 的顶层 `code=200` 不应单独作为操作成功依据。按官方响应契约检查 `data[].result.api_result`：

```json
{"code":200,"message":"success","data":[{"url":"lifeup://api/item?id=1","result":{"api_result":true}}]}
```

**常用 `lifeup://api/…` 方法**（完整见官方 [API 列表](https://wiki.lifeupapp.fun/zh-cn/guide/api.md)）：

| 动作 | 方法 |
| --- | --- |
| 完成任务 | `complete` |
| 放弃任务 | `give_up` |
| 购买商品 | `purchase_item` |
| 使用物品 | `use_item` |
| 合成 | `synthesize` |
| 新建任务 | `add_task` |
| 发放奖励（金币 / 经验 / 物品等） | `reward` |
| 开箱 | `loot_box` |
| 番茄计时控制 | `pomodoro_timer` |
| 完成 / 领取成就奖励 | `complete_achievement?id=…`（人升 v1.105.1+） |
| 解锁成就条件 | `unlock_condition?id=…` |
| 跳转页面 | `goto?page=…` |

> 💡 **命名注意**：**原生 URL Scheme 方法名 ≠ MCP 工具名**。原生里是 `complete`，MCP 工具里才可能使用 `complete_task` 等工具名——别写混。领取成就奖励使用 `complete_achievement`，不要用发放通用奖励的 `reward` 代替。

## 4. 关键字段取值

| 接口 | 字段 | 取值 |
| --- | --- | --- |
| `/tasks` `/history` | `status` | `0` 未完成 · `1` 已完成 · `2` 逾期 · `3` 放弃 |
| `/tasks` | `frequency` | `0` 一次 · `1` 每日 · `N>1` 每 N 天 · `-1` 无限制 · `-3` 艾宾浩斯 · `-4` 每月 · `-5` 每年 |
| `/tasks` | `weekdays` | `"1,3,5"`（1=周一 … 7=周日）；非每周几为空；**v1.106.0+** |
| `/achievements` | `status` | `0` 未解锁 · `1` 已解锁未领奖 · `2` 已解锁已领奖；完成 / 领取奖励调用 `complete_achievement`（v1.105.1+） |
| `/achievements` | `type` | `0` 普通 · `1` 子分类 |
| `/achievement_categories` | `type` | `0` 用户 · `1` 系统 |
| `/feelings` | `type` | `0` 任务 · `1` 成就 · `2` 纯文本 · `3` 使用物品 |
| `/feelings` | `isFav` | JSON `true/false`（Provider 原始值为 0/1） |
| `/items_categories` | `hidden` / `inventoryHidden` | `0` 显示 · `1` 隐藏（两列独立） |
| `/synthesis_categories` | `hidden` | `0` 显示 · `1` 隐藏 |
| `/skills` | `type` | `0` 用户属性 · `1` 力量 · `2` 学识 · `3` 魅力 · `4` 耐力 · `5` 活力 · `6` 创造 |
| `/tasks_categories` | `status` | `0` 正常 · `1` 已归档 |
| `/tasks_categories` | `type` | `<10` 普通 · `10` 每日 · `11` 每周 · `12` 每月 · `20` 进行中 |

> ⚠️ **任务的 `id` 每个周期会变，`gid` 不变** —— 跨周期识别 / 缓存请用 **`gid`**。
> 写 URL Scheme 用 **snake_case**（`category_id` / `stock_number` / `title_color_string`）；Cloud JSON 读出来是 **camelCase**。

## 5. 连通自测

```bash
curl http://192.168.1.23:13276/info
# 返回含 appVersionName / cloudVersionName 即通
```
