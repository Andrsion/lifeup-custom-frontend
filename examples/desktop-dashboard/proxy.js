/**
 * 人升 · 自定义界面 —— 最小本地代理（零依赖，只需 Node.js 20+）
 *
 * 作用：
 *   1) 把前端发到 /cloud/* 的请求，转发给手机上的「云人升」（默认 :13276）
 *      —— 解决浏览器 CORS，并让 Token 留在本地、不进浏览器。
 *   2) 顺带把当前目录当作静态站点跑，直接提供 index.html。
 *
 * 用法：
 *   1) 复制 config.example.json 为 config.json，填上你手机的 IP
 *   2) node proxy.js   （或双击 start.bat / start.command）
 *   3) 浏览器打开 http://localhost:8787
 *
 * ⚠️ 接口以官方为准：https://wiki.lifeupapp.fun/zh-cn/guide/api_cloud.md
 */
const http = require("http");
const fs = require("fs");
const path = require("path");

const cfgPath = path.join(__dirname, "config.json");
if (!fs.existsSync(cfgPath)) {
  console.error("✖ 找不到 config.json，请先复制 config.example.json 为 config.json 并填写手机 IP。");
  process.exit(1);
}
const cfg = JSON.parse(fs.readFileSync(cfgPath, "utf8"));
const [HOST, PORT = "13276"] = String(cfg.host || "").split(":");
const LISTEN = cfg.port || 8787;

const MIME = {
  ".html": "text/html", ".js": "text/javascript", ".css": "text/css",
  ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png",
  ".jpg": "image/jpeg", ".ico": "image/x-icon", ".woff2": "font/woff2"
};

function json(res, code, obj) {
  res.writeHead(code, { "Content-Type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(obj));
}

const server = http.createServer((req, res) => {
  const u = new URL(req.url, `http://${req.headers.host}`);

  // —— 1) 代理：/cloud/* → 云人升 ——
  if (u.pathname.startsWith("/cloud/")) {
    const upstreamPath = u.pathname.slice("/cloud".length) + (u.search || "");
    const headers = {};
    // 若云人升设了访问 Token：原样放进请求头（不要加 "Bearer "）
    if (cfg.tokenHeader && cfg.token) headers[cfg.tokenHeader] = cfg.token;

    const preq = http.request(
      { host: HOST, port: PORT, method: req.method, path: upstreamPath, headers },
      (pres) => {
        res.writeHead(pres.statusCode, {
          "Content-Type": "application/json; charset=utf-8",
          "Access-Control-Allow-Origin": "*"
        });
        pres.pipe(res);
      }
    );
    preq.on("error", (e) => json(res, 502, {
      code: -1,
      message: "连不上云人升：" + e.message + `（检查 config.json 的 host 是否为 ${HOST}:${PORT}，且手机与电脑同一 Wi‑Fi）`
    }));
    if (req.method === "POST" || req.method === "PUT") req.pipe(preq);
    else preq.end();
    return;
  }

  // —— 2) 静态站点 ——
  let rel = u.pathname === "/" ? "/index.html" : u.pathname;
  const file = path.join(__dirname, decodeURIComponent(rel));
  if (!file.startsWith(__dirname) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
    res.writeHead(404); return res.end("Not found");
  }
  const ext = path.extname(file).toLowerCase();
  res.writeHead(200, { "Content-Type": (MIME[ext] || "application/octet-stream") + "; charset=utf-8" });
  fs.createReadStream(file).pipe(res);
});

server.listen(LISTEN, () => {
  console.log("✔ 已启动：");
  console.log(`   前端      http://localhost:${LISTEN}`);
  console.log(`   云人升    http://${HOST}:${PORT}  (config.json 里可改)`);
  console.log("   按 Ctrl+C 停止");
});
