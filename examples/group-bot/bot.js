/**
 * 群机器人骨架：把群里的「打卡」消息，变成人升任务完成。
 *
 * 这是个「平台无关」的核心：真正的机器人框架（QQ / 微信 / Telegram / Discord…）
 * 只需要在收到消息时调用本文件的 handleMessage(user, text) 即可。
 *
 * 它默认用「按任务名完成」：lifeup://api/complete?name=任务名
 * —— 所以先在《人升》里建好同名任务；群友发「打卡 喝水」就会完成「喝水」。
 *
 * ⚠️ 写操作不幂等，别对同一条消息重复调用（自己去重）。
 * ⚠️ 接口以官方为准：https://wiki.lifeupapp.fun/zh-cn/guide/api_cloud.md
 */
const http = require("http");
const fs = require("fs");
const path = require("path");

const cfgPath = path.join(__dirname, "config.json");
if (!fs.existsSync(cfgPath)) {
  console.error("缺少 config.json，请复制 config.example.json 并填写手机 IP。");
  process.exit(1);
}
const CFG = JSON.parse(fs.readFileSync(cfgPath, "utf8"));
const [HOST, PORT = "13276"] = String(CFG.host || "").split(":");

function request(method, urlPath, body) {
  return new Promise((resolve, reject) => {
    const headers = {};
    if (CFG.tokenHeader && CFG.token) headers[CFG.tokenHeader] = CFG.token; // 原始 Token，不加 Bearer
    if (body) { headers["Content-Type"] = "application/json"; headers["Content-Length"] = Buffer.byteLength(body); }
    const req = http.request({ host: HOST, port: PORT, method, path: urlPath, headers }, (res) => {
      let data = "";
      res.on("data", (c) => (data += c));
      res.on("end", () => {
        let j; try { j = JSON.parse(data); } catch (e) { return reject(new Error("返回非 JSON：" + data.slice(0, 120))); }
        resolve(j);
      });
    });
    req.on("error", reject);
    if (body) req.write(body);
    req.end();
  });
}

const read = (p) => request("GET", p);
const doApi = (lifeupUrl) =>
  request("GET", "/api/contentprovider?url=" + encodeURIComponent(lifeupUrl));

/** 读取未完成任务清单（bot 可用来做「今日待办」） */
async function listOpenTasks() {
  const j = await read("/tasks?limit=200");
  if (j.code !== 200) throw new Error(mapErr(j.code));
  return (j.data || []).filter((t) => t.status === 0);
}

/**
 * 处理一条群消息。
 * @returns {string|null} 要回复给群友的文案；null = 不处理
 */
async function handleMessage(user, text) {
  const m = String(text).trim().match(/^打卡\s*(.+)$/);
  if (!m) return null;                       // 不是打卡消息，交给别的逻辑
  const name = m[1].trim();
  try {
    const j = await doApi(`lifeup://api/complete?name=${encodeURIComponent(name)}`);
    const r = j.data && j.data[0] && j.data[0].result;
    if (r && r.api_result === false) {
      return `@${user} 打卡失败：${r.error_message || "任务不存在或参数不对"}`;
    }
    return `✅ @${user} 已完成「${name}」，金币已到账！`;
  } catch (e) {
    return `@${user} 打卡出错：${e.message}（检查手机是否在线、是否同一 Wi‑Fi）`;
  }
}

function mapErr(code) {
  return { 10001: "人升没运行 / 未授「读取人升数据」", 10002: "读取数据失败", 401: "Token 不对" }[code] || ("错误码 " + code);
}

module.exports = { handleMessage, listOpenTasks, doApi, read };

// 自测：node bot.js 打卡 喝水
if (require.main === module) {
  const [, , ...rest] = process.argv;
  if (rest[0]) {
    handleMessage("你", rest.join(" ")).then((msg) => console.log(msg || "（不是打卡消息）"));
  } else {
    listOpenTasks().then((list) => {
      console.log(`当前未完成任务 ${list.length} 个：`);
      list.slice(0, 20).forEach((t) => console.log(` - ${t.name}  #${t.gid ?? t.id}`));
    }).catch((e) => console.error("出错：", e.message));
  }
}
