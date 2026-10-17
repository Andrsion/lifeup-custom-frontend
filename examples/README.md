# 可运行示例（Examples）

理论看 [实现方案](../docs/custom-ui-ai-mcp.md)，这里给你**能直接跑**的样板 —— 复制、改配置、双击即用。

| 示例 | 完成程度 | 形态 | 适合 |
| --- | --- | --- | --- |
| [**minimal-html**](minimal-html/) | **可直接运行** | 单文件看板 + 本地代理 | 第一次上手 / 想要最简的 |
| [**desktop-dashboard**](desktop-dashboard/) | **可直接运行** | 大屏看板（大字号、自动刷新） | 平板 / 显示器常驻 |
| [**group-bot**](group-bot/) | **核心可自测，需接平台** | Node 机器人核心逻辑（打卡 → 完成任务） | 接 QQ / 微信 / 任意聊天机器人 |

## 共同前提

- 手机：**人升 v1.106.0+** ＋ **云人升 3.0.0+**，云人升里开「**读取人升数据**」
- 电脑：**Node.js 20+**；与手机**同一 Wi‑Fi**
- 两个看板示例是「**改 config.json → 双击启动 → 打开浏览器**」；`group-bot` 是可自测的核心模块，需要接入你实际使用的聊天平台框架。

### 群机器人核心自测

在 `examples/group-bot/` 中复制并填写 `config.json` 后，可运行 `node bot.js` 查看未完成任务；`node bot.js 打卡 任务名` 会真实调用完成任务接口，请只在确认要执行时运行。写操作结果不明确时不要自动重试。

## 首次运行诊断

在仓库根目录执行：

```bash
node scripts/doctor.js examples/minimal-html
```

工具只检查配置并调用官方文档列出的只读 `GET /info`，不会完成任务、发奖励或购买商品。接口行为以官方文档为准。

## 三层架构（看板示例）

```
你的前端（任意皮肤）
  ↕  HTTP
本地代理（proxy.js：同源转发 + 本地保存 Token；默认只监听回环地址）
  ↕  HTTP :13276
云人升（手机端）
  ↕  ContentProvider
人升 App
```

> ⚠️ 接口以官方为准：<https://wiki.lifeupapp.fun/zh-cn/guide/api_cloud.md>。
> 连不上 / 报错，先看 [排错](../docs/troubleshooting.md)。

## 想自己写？

把 [实现方案](../docs/custom-ui-ai-mcp.md) 整篇丢给你本地运行的 AI 工具（Trae / 通义灵码 / CodeBuddy / WorkBuddy…），照它做的即可。
