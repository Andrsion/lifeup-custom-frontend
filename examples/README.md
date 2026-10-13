# 可运行示例（Examples）

理论看 [实现方案](../docs/custom-ui-ai-mcp.md)，这里给你**能直接跑**的样板 —— 复制、改配置、双击即用。

| 示例 | 形态 | 适合 |
| --- | --- | --- |
| [**minimal-html**](minimal-html/) | 单文件看板 + 本地代理 | 第一次上手 / 想要最简的 |
| [**desktop-dashboard**](desktop-dashboard/) | 大屏看板（大字号、自动刷新） | 平板 / 显示器常驻 |
| [**group-bot**](group-bot/) | Node 机器人骨架（打卡 → 完成任务） | 接 QQ / 微信 / 任意聊天机器人 |

## 共同前提

- 手机：**人升 v1.106.0+** ＋ **云人升 3.0.0+**，云人升里开「**读取人升数据**」
- 电脑：**Node.js 20+**；与手机**同一 Wi‑Fi**
- 每个示例都是「**改 config.json → 双击启动 → 打开浏览器**」

## 三层架构（所有示例都一样）

```
你的前端（任意皮肤）
  ↕  HTTP
本地代理（proxy.js：解决 CORS + 藏 Token）
  ↕  HTTP :13276
云人升（手机端）
  ↕  ContentProvider
人升 App
```

> ⚠️ 接口以官方为准：<https://wiki.lifeupapp.fun/zh-cn/guide/api_cloud.md>。
> 连不上 / 报错，先看 [排错](../docs/troubleshooting.md)。

## 想自己写？

把 [实现方案](../docs/custom-ui-ai-mcp.md) 整篇丢给你本地运行的 AI 工具（Trae / 通义灵码 / CodeBuddy / WorkBuddy…），照它做的即可。
