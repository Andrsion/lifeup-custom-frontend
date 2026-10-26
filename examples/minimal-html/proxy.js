/**
 * 人升自定义界面本地代理（Node.js 20+，零依赖）。
 * 安全默认值：仅监听回环地址；仅代理到 config.json 中指定的单一上游；
 * 只允许官方云人升 HTTP 接口需要的 GET/POST；不提供跨域开放访问。
 *
 * 官方接口文档：https://wiki.lifeupapp.fun/zh-cn/guide/api_cloud.md
 * 文档若与官方 SDK/服务端实现不一致，以官方源码为准。
 */
"use strict";
const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");

const ROOT = path.resolve(__dirname);
const cfgPath = path.join(ROOT, "config.json");
if (!fs.existsSync(cfgPath)) {
  console.error("✖ 缺少 config.json。请复制 config.example.json 并填写云人升地址。");
  process.exit(1);
}

let cfg;
try {
  cfg = JSON.parse(fs.readFileSync(cfgPath, "utf8"));
} catch {
  console.error("✖ config.json 不是合法 JSON。");
  process.exit(1);
}

const HOST_RE = /^([^:\s/]+)(?::(\d{1,5}))?$/;
const hostInput = String(cfg.host || "").trim();
const hostParts = hostInput.match(HOST_RE);
if (!hostParts) {
  console.error("✖ config.json 的 host 格式应为手机 IP 或 IP:端口。");
  process.exit(1);
}
let UPSTREAM_HOST = hostParts[1];
let UPSTREAM_PORT = Number(hostParts[2] || 13276);
if (!Number.isInteger(UPSTREAM_PORT) || UPSTREAM_PORT < 1 || UPSTREAM_PORT > 65535) {
  console.error("✖ 上游端口无效。");
  process.exit(1);
}
const LISTEN_PORT = Number(cfg.port ?? 8787);
if (!Number.isInteger(LISTEN_PORT) || LISTEN_PORT < 1 || LISTEN_PORT > 65535) {
  console.error("✖ 本地端口无效。");
  process.exit(1);
}
const LISTEN_HOST = String(cfg.listenHost || "127.0.0.1");
if (!["127.0.0.1", "::1", "localhost"].includes(LISTEN_HOST)) {
  console.error("✖ 默认仅允许监听本机回环地址。若确需局域网访问，请先自行评估安全风险并修改配置与访问控制。");
  process.exit(1);
}

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".ico": "image/x-icon",
  ".woff2": "font/woff2"
};
const TOKEN_HEADER = String(cfg.tokenHeader || "").trim();
const TOKEN = String(cfg.token || "");
if (TOKEN_HEADER && !/^[!#$%&'*+.^_`|~0-9A-Za-z-]+$/.test(TOKEN_HEADER)) {
  console.error("✖ tokenHeader 不是合法的 HTTP 请求头名称。");
  process.exit(1);
}
const FORBIDDEN_TOKEN_HEADERS = new Set(["host", "connection", "content-length", "transfer-encoding", "upgrade", "proxy-connection", "keep-alive", "te", "trailer"]);
if (FORBIDDEN_TOKEN_HEADERS.has(TOKEN_HEADER.toLowerCase())) {
  console.error("✖ tokenHeader 不能覆盖 Host 或 Connection 请求头。");
  process.exit(1);
}

function send(res, status, message) {
  if (res.headersSent) return res.destroy();
  res.writeHead(status, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" });
  res.end(JSON.stringify({ code: -1, message }));
}

function isLoopbackHostHeader(value) {
  if (!value) return false;
  try {
    const parsed = new URL("http://" + value);
    return ["localhost", "127.0.0.1", "[::1]"].includes(parsed.hostname);
  } catch {
    return false;
  }
}

const server = http.createServer((req, res) => {
  // 防止 DNS rebinding 将本地代理暴露给其他网页。
  if (!isLoopbackHostHeader(req.headers.host)) return send(res, 403, "仅允许通过 localhost / 127.0.0.1 访问。");
  if (req.headers.origin) {
    try {
      const origin = new URL(req.headers.origin);
      if (origin.protocol !== "http:" || origin.host !== req.headers.host) {
        return send(res, 403, "跨来源请求已拒绝。");
      }
    } catch {
      return send(res, 403, "Origin 请求头无效。");
    }
  }

  let url;
  try {
    url = new URL(req.url, "http://" + req.headers.host);
  } catch {
    return send(res, 400, "请求 URL 无效。");
  }

  if (url.pathname === "/__upstream") {
    const json = (status, data) => { res.writeHead(status, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" }); res.end(JSON.stringify(data)); };
    if (!["GET", "POST"].includes(req.method)) return json(405, { error: "只允许 GET 和 POST。" });
    if (req.method === "GET") return json(200, { host: UPSTREAM_HOST, port: UPSTREAM_PORT });
    if (!/^application\/json(?:\s*;|$)/i.test(req.headers["content-type"] || "")) return json(415, { error: "Content-Type 必须为 application/json。" });
    let raw = "", tooLarge = false;
    req.on("data", chunk => { if (tooLarge) return; raw += chunk; if (Buffer.byteLength(raw, "utf8") > 512) { tooLarge = true; json(413, { error: "请求体过大。" }); } });
    req.on("end", () => {
      if (tooLarge || res.writableEnded) return;
      let body; try { body = JSON.parse(raw || "{}"); } catch { return json(400, { error: "请求体不是合法 JSON。" }); }
      const parts = String(body.host || "").trim().match(HOST_RE);
      if (!parts) return json(400, { error: "地址格式应为 手机IP 或 手机IP:端口" });
      const port = Number(parts[2] || 13276);
      if (!Number.isInteger(port) || port < 1 || port > 65535) return json(400, { error: "端口无效。" });
      UPSTREAM_HOST = parts[1]; UPSTREAM_PORT = port;
      json(200, { host: UPSTREAM_HOST, port: UPSTREAM_PORT });
    });
    return;
  }

  if (url.pathname.startsWith("/cloud/")) {
    if (!["GET", "POST"].includes(req.method)) return send(res, 405, "代理仅允许 GET 和 POST。");
    const upstreamPath = url.pathname.slice("/cloud".length) + url.search;
    if (!upstreamPath.startsWith("/") || upstreamPath.startsWith("//") || /\\/.test(upstreamPath)) {
      return send(res, 400, "上游路径无效。");
    }

    const headers = { Accept: req.headers.accept || "application/json" };
    if (TOKEN_HEADER && TOKEN) headers[TOKEN_HEADER] = TOKEN;
    if (req.method === "POST" && req.headers["content-type"]) headers["content-type"] = req.headers["content-type"];

    const upstream = http.request({
      host: UPSTREAM_HOST,
      port: UPSTREAM_PORT,
      method: req.method,
      path: upstreamPath,
      headers,
      timeout: 10000
    }, (upstreamRes) => {
      const responseHeaders = {
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff"
      };
      if (upstreamRes.headers["content-type"]) responseHeaders["Content-Type"] = upstreamRes.headers["content-type"];
      res.writeHead(upstreamRes.statusCode || 502, responseHeaders);
      upstreamRes.pipe(res);
    });

    upstream.on("timeout", () => upstream.destroy(new Error("请求云人升超时")));
    upstream.on("error", (error) => send(res, 502, "无法连接云人升或请求超时。请检查手机网络、IP、端口和服务状态。"));
    req.on("aborted", () => upstream.destroy());
    if (req.method === "POST") req.pipe(upstream);
    else upstream.end();
    return;
  }

  if (!["GET", "HEAD"].includes(req.method)) return send(res, 405, "静态文件仅允许 GET 和 HEAD。");
  let decoded;
  try {
    decoded = decodeURIComponent(url.pathname);
  } catch {
    return send(res, 400, "文件路径编码无效。");
  }
  if (decoded.includes("\0") || decoded.includes("\\")) return send(res, 400, "文件路径无效。");

  const relative = decoded === "/" ? "index.html" : decoded.replace(/^\/+/, "");
  const file = path.resolve(ROOT, relative);
  if (file !== ROOT && !file.startsWith(ROOT + path.sep)) return send(res, 403, "禁止访问目录外文件。");
  // 不通过 Web 暴露配置、隐藏文件或源代码仓库元数据。
  const relParts = path.relative(ROOT, file).split(path.sep);
  if (relParts.some(part => part.startsWith(".")) || path.basename(file) === "config.json") {
    return send(res, 404, "Not found");
  }
  let stat;
  try {
    stat = fs.statSync(file);
  } catch {
    return send(res, 404, "Not found");
  }
  if (!stat.isFile()) return send(res, 404, "Not found");

  const headers = {
    "Content-Type": MIME[path.extname(file).toLowerCase()] || "application/octet-stream",
    "Content-Length": stat.size,
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": "default-src 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
  };
  res.writeHead(200, headers);
  if (req.method === "HEAD") return res.end();
  fs.createReadStream(file).on("error", () => {
    if (!res.headersSent) send(res, 500, "读取文件失败。");
    else res.destroy();
  }).pipe(res);
});

server.requestTimeout = 15000;
server.headersTimeout = 10000;
server.listen(LISTEN_PORT, LISTEN_HOST, () => {
  console.log("✔ 本地看板代理已启动");
  console.log(`   页面：http://127.0.0.1:${LISTEN_PORT}`);
  console.log(`   云人升上游：http://${UPSTREAM_HOST}:${UPSTREAM_PORT}`);
  console.log("   地址可在页面顶栏直接改（临时生效，不写入 config.json）。");
  console.log("   默认只接受本机访问；按 Ctrl+C 停止。");
});
