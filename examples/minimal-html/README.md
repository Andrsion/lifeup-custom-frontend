# 最小可运行示例：单文件看板

一个**能直接跑起来**的人升自定义界面：顶部显示金币 / 属性，下面列出未完成任务，点「完成」即可打卡。
它是 [实现方案](../../docs/custom-ui-ai-mcp.md) 里「三层架构」的最小落地：**前端 + 一层本地代理 + 云人升**。

```
index.html   ← 前端（换个皮肤就是你的主题）
proxy.js     ← 本地代理：转发 /cloud/* 到云人升 + 解决 CORS + 藏 Token
config.json  ← 你的手机 IP（从 config.example.json 复制）
start.bat / start.command  ← 双击启动
```

## 跑起来

1. **手机侧**：装 **人升 v1.106.0+** 与 **云人升 3.0.0+**；人升开「设置 → 实验」，云人升里开「**读取人升数据**」。
2. **电脑侧**：装 **Node.js 20+**。
3. 同 Wi‑Fi 下，查手机 IP（云人升首页会显示 `IP:13276`）。
4. 复制 `config.example.json` 为 `config.json`，把 `host` 改成你的 `IP:13276`。
5. 双击 **`start.bat`**（Windows）或 **`start.command`**（macOS，首次可能需 `chmod +x start.command`）；或命令行 `node proxy.js`。
6. 浏览器打开 **http://localhost:8787**。

## 换主题（很简单）

打开 `index.html`，改顶部 `UI` 对象即可：

```js
const UI = { coin: "金币", tasks: "任务", done: "完成", empty: "今天没有待办 🎉" };
```

想更彻底（清单名 / 货币名 / 文案 / 配色），照 [世界观 / 主题参考](../../docs/samples.md) 的「换名对照表」来改。
（例：动物森友会主题 → 金币改「铃钱」、任务改「岛屿待办」。）

## 说明

- 这里**只用到了「读 + 完成」两个动作**。更多动作（商店购买 `purchase_item`、开箱 `loot_box`、合成 `synthesize`…）见
  [接口速查表](../../docs/api-cheatsheet.md)。
- **写操作不幂等，别自动重试**；重试逻辑请加在提示层，不要静默重发。
- 连不上先看 [排错](../../docs/troubleshooting.md)：常见是**同一 Wi‑Fi**、**云人升没开「读取数据」**、或 **IP 变了**。
