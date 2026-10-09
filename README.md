## ⚠️ 先分清：这不是「人升自带的外观设置」

| 你想干嘛 | 该去哪儿 |
| --- | --- |
| 调人升**自带**的外观（主题色、简洁模式、Material You、卡片背景） | App 内「**设置**」，或 `lifeup://api/app_settings` 接口（v1.98+） |
| 在**人升之外**搭自己的界面（看板 / AI 助手 / 机器人） | ✅ **本项目** |

> 本项目**不是**人升自带的外观 / 主题设置，而是**在人升 App 之外**、基于「云人升」HTTP 服务另做的一层**第三方界面**。

# 自定义人升 · 自定义界面 + AI + MCP 实现方案

> 在《人升》(LifeUp) 之上做一层**「自定义界面」** —— 自己搭看板、接 AI 助手、做桌面 / 语音 / 群机器人外壳。
>
> 所有数据与规则都在**手机端人升 App** 里跑，网页只做「展示 + 转发」。**不需要会写代码** —— 把方案整篇喂给 AI 工具即可。

---

## 🤖 直接交给 AI（推荐入口）

把下面这段**整段复制**给你用的 AI / Agent（把 `<>` 换成你自己的信息）：

```
我要做一个人升（LifeUp）的自定义界面。请先完整读取这份方案：
https://gitee.com/Andrsion/lifeup-custom-frontend/raw/main/docs/custom-ui-ai-mcp.md
读完直接按文档里的「快速上手」开始做，别再问我"你想做什么"。
我的玩法体系：<主题 / 货币叫法 / 清单叫法；不填则读我的 MCP 数据>
我要的页面：<任务 + 商店 + 金币属性栏>
我的环境：，已装 Node.js 20+ 和
规则：① 先读文档再写代码，接口以文档里的官方链接为准，不要臆造；② 不确定就按文档「开工前自检」处理；③ 做成双击就能启动，最后给我用法说明。
```

**给 AI 的文档链接**（任选其一，raw 是纯文本、最好抓）：

- **Gitee（国内推荐）**：`https://gitee.com/Andrsion/lifeup-custom-frontend/raw/main/docs/custom-ui-ai-mcp.md`
- **GitHub**：`https://raw.githubusercontent.com/Andrsion/lifeup-custom-frontend/main/docs/custom-ui-ai-mcp.md`

> ⚠️ 若 AI 反馈"读不了链接"：改用**网页版**（把 `raw/main` 换成 `blob/main`），或干脆把文档内容**粘贴**给它。
> 分支名是 **`main`**（写成 `master` 会 404）。

## 这是什么

《人升》是一款把任务 / 习惯变成 RPG 的游戏化待办 App。它配套的**「云人升」**会在手机上开一个 HTTP 服务（局域网，默认端口 `13276`），于是你可以在它之上做一层自己的界面：

- 🎨 **任意皮肤的看板**：动物森友会 / 修仙 / 赛博朋克……（Web、桌面、平板大屏）
- 🤖 **AI 助手**：说一句「把今天的日常做完」，AI 自动调接口完成
- 👥 **社群机器人**：群友打卡 → 自动建任务 / 发奖励
- 🔌 **官方 MCP**：配一次，就能用人话直接操作人升

## 快速开始（三步）

| 步骤 | 做什么 |
| --- | --- |
| 1️⃣ 手机侧 | 装 **人升 v1.106.0+** 与 **云人升 3.0.0+**；人升开「设置 → 实验 → MCP」，云人升里开「读取人升数据」；手机与电脑连**同一个 Wi-Fi** |
| 2️⃣ 电脑侧 | 挑一个**在你电脑本地运行**的 AI 工具（Trae / 通义灵码 / CodeBuddy / WorkBuddy / dsh…），并装好 **Node.js 20+** |
| 3️⃣ 开做 | 把 👉 **[docs/custom-ui-ai-mcp.md](docs/custom-ui-ai-mcp.md)** **整篇复制**，丢给第 2 步的工具，照它说的做 |

> ⚠️ 别用「云端生成 + 云端托管」的平台（秒哒、Bolt.new、v0、Lovable 等）—— 它们访问不到你家 Wi-Fi 里的手机。

## 文档

| 文档 | 内容 |
| --- | --- |
| **[实现方案](docs/custom-ui-ai-mcp.md)** | 定位 · 快速上手（含可粘贴的提示词）· 原理与接口（读 / 写 / AI 两条接法）· 坑与限制 · 客户端接入 MCP（WorkBuddy / dsh）· **附录：组件清单 & 灵感库** |
| **[世界观 / 主题参考](docs/samples.md)** | 可借用的世界观与主题（大众 IP / 社区体系 / 同类产品）+ 8 个「换名对照表」案例 |
| **[地球 Online 梗词表](docs/earth-online-glossary.md)** | 用游戏术语解构人生的公共梗词速查 + 可直接用的文案模板 |

## 权威文档（一切以官方为准）

- 云人升 HTTP 接口 · <https://wiki.lifeupapp.fun/zh-cn/guide/api_cloud.md>
- MCP & Skills · <https://wiki.lifeupapp.fun/zh-cn/guide/api_mcp.md>
- 官方 SDK / skills 源码 · <https://github.com/Ayagikei/LifeUp-SDK>
- 人升 Wiki · <https://wiki.lifeupapp.fun/>

## 版本门槛

- **人升 v1.106.0 正式**（2026/09/23）或更高
- **云人升 v3.0.0+**

## 许可

本文档采用 **CC BY-NC-SA 4.0** 许可：可自由转载 / 改编，需署名、非商业、相同方式共享。详见 [LICENSE](LICENSE)。

---

> 本仓库为社区整理的公开镜像版，非官方仓库；接口与参数细节**以官方文档为准**。
