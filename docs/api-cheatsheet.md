# 云人升 HTTP 接口 · 速查表

> ⚠️ 本表仅供**速查 / 防臆造**。**一切以官方文档为准**：<https://wiki.lifeupapp.fun/zh-cn/guide/api_cloud.md>
>
> 前置：人升 **v1.91+**（本方案建议 **v1.106.0+**）＋ **云人升**；先在云人升里开「**读取人升数据**」。地址形如 `http://<手机IP>:13276`（局域网）。

## 0. 基础

- 主机：`http://{手机IP}:13276`（默认端口 **13276**，以云人升显示为准）
- 统一响应：`{ code, message, data }`。**`code=200` 只表示传输成功**
  - `10001`：人升未运行 / 未授「读取数据」
  - `10002`：ContentProvider 查询失败
  - `401`：Token 错误（仅当云人升设了访问 Token）
- 列表接口 `data` 是**数组**；`/coin`、`/info` 的 `data` 是**对象**
- 分页参数：`offset`、`limit`（默认 limit 100，看返回里有没有更多）

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
GET /items/{清单id}
GET /items_categories[?include_hidden=true]
```

**成就**

```
GET /achievements
GET /achievements/{清单id}
GET /achievement_categories
```

**感想 / 合成 / 属性**

```
GET /feelings?offset=&limit=
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
GET /coin_records
GET /inventory_records
GET /exp_records
GET /step_records
GET /level_defines
GET /statistics?time_range_start=&time_range_end=
GET /events?after=&limit=50   ← 广播事件（GET 轮询）
ws://{host}/events?after={id} ← 广播事件（WebSocket 推送）
```

**图片**

```
GET /files/{url}
```

## 2. 写（调用 `lifeup://api/…`）

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
> ⚠️ `/api/contentprovider` 的顶层 `code=200` 只代表**送达**，业务成败要再看 `data[].result.api_result`：

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

## 3. 关键字段取值

| 接口 | 字段 | 取值 |
| --- | --- | --- |
| `/tasks` `/history` | `status` | `0` 未完成 · `1` 已完成 · `2` 逾期 · `3` 放弃 |
| `/tasks` | `frequency` | `0` 一次 · `1` 每日 · `N>1` 每 N 天 · `-1` 无限制 · `-3` 艾宾浩斯 · `-4` 每月 · `-5` 每年 |
| `/tasks` | `weekdays` | `"1,3,5"`（1=周一 … 7=周日）；非每周几为空；**v1.106.0+** |
| `/achievements` | `status` | `0` 未解锁 · `1` 已解锁未领奖 · `2` 已解锁已领奖 |
| `/skills` | `type` | `0` 用户属性 · `1` 力量 · `2` 学识 · `3` 魅力 · `4` 耐力 · `5` 活力 · `6` 创造 |
| `/tasks_categories` | `type` | `<10` 普通 · `10` 每日 · `11` 每周 · `12` 每月 · `20` 进行中 |

> ⚠️ **任务的 `id` 每个周期会变，`gid` 不变** —— 跨周期识别 / 缓存请用 **`gid`**。
> 写 URL Scheme 用 **snake_case**（`category_id` / `stock_number` / `title_color_string`）；Cloud JSON 读出来是 **camelCase**。

## 4. 连通自测

```bash
curl http://192.168.1.23:13276/info
# 返回含 appVersionName / cloudVersionName 即通
```
