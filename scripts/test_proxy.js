#!/usr/bin/env node
"use strict";

/**
 * 本地代理集成测试：使用假的上游 HTTP 服务，不访问真实手机或执行人升写操作。
 * 运行：node scripts/test_proxy.js
 */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const http = require("node:http");
const { spawn } = require("node:child_process");

const ROOT = path.resolve(__dirname, "..");
const proxySource = path.join(ROOT, "examples/minimal-html/proxy.js");

function freePort() {
  return new Promise((resolve, reject) => {
    const server = http.createServer();
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      server.close(error => error ? reject(error) : resolve(address.port));
    });
  });
}

function request(port, options = {}, body = "") {
  return new Promise((resolve, reject) => {
    const req = http.request({
      host: "127.0.0.1",
      port,
      method: options.method || "GET",
      path: options.path || "/",
      headers: { ...(options.headers || {}) },
      timeout: 1500
    }, res => {
      let data = "";
      res.setEncoding("utf8");
      res.on("data", chunk => data += chunk);
      res.on("end", () => resolve({ status: res.statusCode, headers: res.headers, body: data }));
    });
    req.on("timeout", () => req.destroy(new Error("test request timed out")));
    req.on("error", reject);
    if (body) req.write(body);
    req.end();
  });
}

async function waitForProxy(port, child) {
  const started = Date.now();
  while (Date.now() - started < 4000) {
    if (child.exitCode !== null) throw new Error("proxy exited early");
    try {
      const response = await request(port);
      if (response.status === 200) return;
    } catch {}
    await new Promise(resolve => setTimeout(resolve, 50));
  }
  throw new Error("proxy did not start in time");
}

(async () => {
  const upstreamPort = await freePort();
  const proxyPort = await freePort();
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), "lifeup-proxy-test-"));
  let child;
  let upstream;
  let capturedToken = null;
  let capturedBody = "";

  try {
    upstream = http.createServer((req, res) => {
      capturedToken = req.headers["x-test-token"] || null;
      let body = "";
      req.on("data", chunk => body += chunk);
      req.on("end", () => {
        capturedBody = body;
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ code: 200, message: "success", data: { test: true } }));
      });
    });
    await new Promise((resolve, reject) => upstream.listen(upstreamPort, "127.0.0.1", resolve).once("error", reject));

    fs.copyFileSync(proxySource, path.join(temp, "proxy.js"));
    fs.writeFileSync(path.join(temp, "config.json"), JSON.stringify({
      host: "127.0.0.1:" + upstreamPort,
      port: proxyPort,
      tokenHeader: "X-Test-Token",
      token: "test-token-only"
    }));
    fs.writeFileSync(path.join(temp, "index.html"), "proxy-test-page");

    child = spawn(process.execPath, [path.join(temp, "proxy.js")], {
      cwd: temp,
      stdio: ["ignore", "ignore", "pipe"]
    });
    await waitForProxy(proxyPort, child);

    const page = await request(proxyPort);
    assert.equal(page.status, 200, "serves the local page");
    assert.equal(page.body, "proxy-test-page");
    assert.equal(page.headers["access-control-allow-origin"], undefined, "does not enable wildcard CORS");

    const hiddenConfig = await request(proxyPort, { path: "/config.json" });
    assert.equal(hiddenConfig.status, 404, "does not expose config.json");

    const traversal = await request(proxyPort, { path: "/..%2fconfig.json" });
    assert.ok([403, 404].includes(traversal.status), "blocks directory traversal");

    const badHost = await request(proxyPort, { headers: { Host: "attacker.example" } });
    assert.equal(badHost.status, 403, "rejects unexpected Host header");

    const badOrigin = await request(proxyPort, { headers: { Origin: "http://attacker.example" } });
    assert.equal(badOrigin.status, 403, "rejects cross-origin requests");

    const badMethod = await request(proxyPort, { method: "PUT", path: "/cloud/info" });
    assert.equal(badMethod.status, 405, "rejects unsupported proxy methods");

    const read = await request(proxyPort, { path: "/cloud/info" });
    assert.equal(read.status, 200);
    assert.equal(capturedToken, "test-token-only", "adds token only to upstream request");
    assert.equal(read.headers["access-control-allow-origin"], undefined, "does not add CORS headers to upstream response");

    const body = JSON.stringify({ urls: ["lifeup://api/toast?text=test"] });
    const write = await request(proxyPort, {
      method: "POST",
      path: "/cloud/api/contentprovider",
      headers: { "Content-Type": "application/json" }
    }, body);
    assert.equal(write.status, 200);
    assert.equal(capturedBody, body, "forwards POST body unchanged");

    console.log("✓ 本地代理集成测试通过（静态资源、配置保护、路径边界、Host/Origin、方法限制、Token 转发、POST body）。");
  } finally {
    if (child && child.exitCode === null) child.kill("SIGTERM");
    if (upstream) await new Promise(resolve => upstream.close(() => resolve()));
    fs.rmSync(temp, { recursive: true, force: true });
  }
})().catch(error => {
  console.error("✖ 本地代理集成测试失败：", error);
  process.exitCode = 1;
});
