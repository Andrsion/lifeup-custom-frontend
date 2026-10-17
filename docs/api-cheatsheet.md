# 云人升 HTTP 接口 · 速查表

> ⚠️ 本表仅供**速查 / 防臆造**。HTTP 路径与响应以 [官方云人升文档](https://wiki.lifeupapp.fun/zh-cn/guide/api_cloud.md) 为准；`lifeup://api/...` 方法名和参数以 [人升官方 API 文档](https://wiki.lifeupapp.fun/zh-cn/guide/api.md) 为准。
>
> 本次核对日期：2026-10-17。官方 Wiki 明确提示部分接口定义可能滞后；如有冲突，请核对其指向的 [LifeUp-SDK 服务端源码](https://github.com/Ayagikei/LifeUp-SDK/blob/main/http/src/main/java/net/lifeupapp/lifeup/http/service/KtorService.kt)。本次核对的 SDK 提交：`ab130079d7d44d1694f96481fa732148860d0b39`。
>
> 前置条件、权限和版本要求请按 [官方云人升 HTTP 文档](https://wiki.lifeupapp.fun/zh-cn/guide/api_cloud.md) 当前内容确认，不要把本表中的版本描述当作高于官方的要求。地址形如 `http://<手机IP>:13276`（局域网）。

## 0. 基础

- 主机：`http://{手机IP}:13276`（默认端口 **13276**，以云人升显示为准）
- 统一响应：`{ code, message, data }`。**`code=200` 只表示传输成功**
  - `10001`：人升未运行 / 未授「读取数据」
  - `10002`：ContentProvider 查询失败
  - Token 认证失败：仅当云人升配置了 Token 时适用；检查当前云人升设置与请求认证方式。HTTP 状态码和 JSON `code` 是不同层次，不把未由官方文档明确保证的状态码当作稳定业务码。
- 列表接口 `data` 是**数组**；`/coin`、`/info` 的 `data` 是**对象**
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

## 2. 分页、权限与版本注意事项

- `/history`：`offset` / `limit` 分页，`gid` 可选，用于筛选某个重复任务组的历史记录；当前官方 SDK 默认 `0` / `100`。
- `/feelings`：分页，当前官方 SDK 默认 `offset=0`、`limit=100`。
- `/pomodoro_records`、`/coin_records`、`/inventory_records`、`/exp_records`、`/step_records`：分页默认 `offset=0`、`limit=100`；可选时间范围参数必须成对传入。
- `/statistics`：只支持可选时间范围，不使用 `offset` / `limit` 分页。
- `/events`：当前 SDK 默认 `after=0`、`limit=50`；事件数据是否产生取决于人升「广播事件」设置，WebSocket 推送另受云人升开关控制。
- 不要擅自给 `/tasks`、`/items`、`/skills` 等接口加分页参数；以各接口官方定义为准。
- 官方云人升文档标注部分接口定义可能滞后；本表的默认值以核对时的官方 SDK `KtorService.kt` 为准，旧版云人升可能不同。
- 版本：官方 HTTP 文档的基础要求为人升 v1.91+ 与最新版云人升；`weekdays` 字段标注人升 v1.106.0+，技能 ContentProvider 查询标注 v1.103.0+。MCP / Skills 的版本门槛属于另一套能力，不要把它当成所有 HTTP 路由的统一最低版本。使用前通过 `/info` 核对当前版本。

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
GET http://{host}:{port}/api?url={ENCODED}
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
| 领奖 | `reward` |
| 开箱 | `loot_box` |
| 番茄钟 | `pomodoro` |
| 跳转页面 | `goto?page=…` |

> 💡 **命名注意**：**原生 URL Scheme 方法名 ≠ MCP 工具名**。原生里是 `complete`，MCP 工具里才叫 `complete_task`——别写混。

## 4. 关键字段取值

| 接口 | 字段 | 取值 |
| --- | --- | --- |
| `/tasks` `/history` | `status` | `0` 未完成 · `1` 已完成 · `2` 逾期 · `3` 放弃 |
| `/tasks` | `frequency` | `0` 一次 · `1` 每日 · `N>1` 每 N 天 · `-1` 无限制 · `-3` 艾宾浩斯 · `-4` 每月 · `-5` 每年 |
| `/tasks` | `weekdays` | `"1,3,5"`（1=周一 … 7=周日）；非每周几为空；**v1.106.0+** |
| `/achievements` | `status` | `0` 未解锁 · `1` 已解锁未领奖 · `2` 已解锁已领奖 |
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

## 6. 连通自测

```bash
curl http://192.168.1.23:13276/info
# 返回含 appVersionName / cloudVersionName 即通
```
