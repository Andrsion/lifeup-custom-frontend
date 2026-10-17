#!/usr/bin/env node
"use strict";

/**
 * 只读诊断工具：检查配置、TCP 连通性，并读取官方文档列出的 /info。
 * 不会调用任何 LifeUp 写操作。
 *
 * 用法：node doctor.js [示例目录]
 * 示例：node doctor.js examples/minimal-html
 * 官方接口文档：https://wiki.lifeupapp.fun/zh-cn/guide/api_cloud.md
 */
const fs = require("node:fs");
const path = require("node:path");
const http = require("node:http");

const target = path.resolve(process.argv[2] || ".");
const configPath = path.join(target, "config.json");
const examplePath = path.join(target, "config.example.json");

function fail(message) {
  console.error("✖ " + message);
  process.exitCode = 1;
}

function parseConfig() {
  if (!fs.existsSync(configPath)) {
    fail("找不到 " + configPath + "。请先复制同目录的 config.example.json 为 config.json 并填写云人升地址。");
    if (fs.existsSync(examplePath)) console.log("提示：配置模板存在：" + examplePath);
    return null;
  }
  let config;
  try {
    config = JSON.parse(fs.readFileSync(configPath, "utf8"));
  } catch {
    fail("config.json 不是合法 JSON。");
    return null;
  }
  const match = String(config.host || "").trim().match(/^([^:\s/]+)(?::(\d{1,5}))?$/);
  if (!match) {
    fail("host 格式无效，应为云人升显示的 IP 或 IP:端口。");
    return null;
  }
  const port = Number(match[2] || 13276);
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    fail("host 中的端口无效。");
    return null;
  }
  if (config.tokenHeader && !config.token) {
    console.warn("⚠️ 配置了 tokenHeader，但 token 为空；请对照云人升官方说明检查。");
  }
  return { config, host: match[1], port };
}

function readInfo(host, port, config) {
  return new Promise((resolve) => {
    const headers = {};
    if (config.tokenHeader && config.token) headers[config.tokenHeader] = config.token;
    const req = http.request({
      host, port, path: "/info", method: "GET", headers, timeout: 5000
    }, (res) => {
      let body = "";
      res.setEncoding("utf8");
      res.on("data", chunk => {
        body += chunk;
        if (body.length > 1024 * 1024) req.destroy(new Error("响应超过 1 MiB"));
      });
      res.on("end", () => {
        let json;
        try { json = JSON.parse(body); } catch {
          return resolve({ ok: false, message: "服务有响应，但返回内容不是 JSON。请按官方文档核对服务地址和接口。" });
        }
        if (res.statusCode < 200 || res.statusCode >= 300) {
          return resolve({ ok: false, message: "HTTP 状态码 " + res.statusCode + "。请核对 Token、地址和官方文档。" });
        }
        if (json.code !== 200) {
          return resolve({ ok: false, message: "接口返回 code=" + String(json.code) + "：" + String(json.message || "未提供错误信息") });
        }
        resolve({ ok: true, data: json.data });
      });
    });
    req.on("timeout", () => req.destroy(new Error("连接超时")));
    req.on("error", error => resolve({ ok: false, message: error.message }));
    req.end();
  });
}

(async () => {
  console.log("LifeUp / 云人升只读诊断");
  console.log("官方接口文档：https://wiki.lifeupapp.fun/zh-cn/guide/api_cloud.md");
  console.log("检查配置文件：" + configPath);
  const parsed = parseConfig();
  if (!parsed) return;
  console.log("✓ 配置 JSON 与 host 格式有效");
  console.log("正在读取官方文档列出的 GET /info（只读）……");
  const result = await readInfo(parsed.host, parsed.port, parsed.config);
  if (!result.ok) {
    fail("连接或读取失败：" + result.message);
    console.log("请确认手机与电脑网络可达、云人升服务正在运行，并以官方文档为准检查权限和配置。");
    return;
  }
  console.log("✓ GET /info 成功");
  if (result.data && typeof result.data === "object") {
    for (const key of ["appVersionName", "cloudVersionName", "apiVersion"]) {
      if (result.data[key] !== undefined) console.log("  " + key + ": " + String(result.data[key]));
    }
  }
  console.log("✓ 只读检查通过；没有执行完成任务、奖励、购买等写操作。");
})().catch(error => {
  fail("诊断工具异常：" + error.message);
});
