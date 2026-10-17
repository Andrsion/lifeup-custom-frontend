# 群机器人骨架（打卡 → 完成任务）

把群里的「**打卡 喝水**」这类消息，变成人升里的**任务完成**。
本示例只给**平台无关的核心**（`bot.js`）——你用哪个聊天平台，就在那里调 `handleMessage(user, text)`。

```
bot.js               ← 核心：收到消息 → 调云人升完成任务
config.example.json  ← 你的手机 IP
```

## 它怎么工作

1. 群友发 `打卡 喝水`；
2. `bot.js` 先读取未完成任务并做**名称完全匹配**；只有唯一匹配时，才使用官方支持的任务标识调用 `lifeup://api/complete?id=...`；
3. 回复群友：`✅ 已完成「喝水」，金币已到账！`

> 所以先在《人升》里建好任务。若找不到唯一的同名未完成任务，机器人会拒绝操作，避免官方 `name` 模糊匹配误完成相似任务。「打卡」前缀可在 `bot.js` 的正则里改。

## 自测

```bash
# 看当前未完成任务
node bot.js
# 试一次打卡（会真的完成任务！）
node bot.js 打卡 喝水
```

## 接你的机器人框架

在收到群消息的地方加一行即可（伪代码）：

```js
const { handleMessage } = require("./bot.js");
const reply = await handleMessage(senderName, text);
if (reply) sendToGroup(reply);   // 交给你的框架发送
```

常见接法：QQ 机器人 / 微信机器人 / Telegram Bot / Discord Bot / 飞书·钉钉机器人——
它们都只是「收发消息的外壳」，核心逻辑用本文件。

## 注意

- **去重**：写操作不幂等。同一个消息 id 别处理两次（框架层做去重）。
- **权限**：读任务列表需要云人升开「读取人升数据」；打卡（写）走的是 URL Scheme 调用接口。
- 想知道更多可做的动作（发奖励 `reward`、开箱 `loot_box`、建任务 `add_task`…），见
  [接口速查表](../../docs/api-cheatsheet.md)。
- 连不上先看 [排错](../../docs/troubleshooting.md)。
