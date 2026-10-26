# AI 施工标准：先核对、再实现、最后验证

> 目标：让 AI 生成的自定义界面不仅看起来正确，而且使用真实数据、遵循官方接口契约，并能在用户本机安全运行。
>
> **权威原则：** 云人升 HTTP 接口、LifeUp URL Scheme、参数、请求体、响应字段、权限和版本要求，必须以官方资料为准。不要根据本仓库旧示例、模型记忆或相似 API 猜测。

## 官方权威来源

1. [云人升 HTTP 接口](https://wiki.lifeupapp.fun/zh-cn/guide/api_cloud.md)
2. [人升开放接口与 URL Scheme](https://wiki.lifeupapp.fun/zh-cn/guide/api.md)
3. [MCP & Skills](https://wiki.lifeupapp.fun/zh-cn/guide/api_mcp.md)
4. [LifeUp-SDK / LifeUp Cloud 官方源码](https://github.com/Ayagikei/LifeUp-SDK)

如果官方文档明确提示某段定义可能滞后，应按该文档指向的官方实现源码核对。若仍无法确认，停止使用该能力并向用户说明不确定点；不要编造参数或把推测写成事实。

## 标准施工流程

### 1. 盘点现状

- 先检查仓库结构、现有配置、运行脚本和依赖。
- 先复用现有项目；除非确有必要，不要重建工程或更换技术栈。
- 不覆盖用户已有配置，不读取或输出 Token、密码和其他秘密。
- 说明预计修改哪些文件，以及会涉及哪些读 / 写能力。

### 2. 核对接口契约

在编写每一个请求前，逐项确认：

- 官方定义的 HTTP 路径和请求方法；
- 查询参数、路径参数或 JSON body 的准确结构；
- 是否需要开启读取权限或其他 App 设置；
- 响应的顶层状态与业务级结果如何区分；
- 适用版本、分页规则、字段可空情况和错误处理；
- 写操作是否可能重复执行，以及超时后如何避免重试。

不要将 URL Scheme 参数、HTTP 查询参数和 JSON body 混为一谈。不要仅因为顶层 HTTP 请求成功就认定游戏内操作成功。

### 3. 先建立真实数据连接

- 优先执行只读检查，确认服务地址和官方文档规定的只读接口可用。
- 先展示实际返回的数据结构，再实现页面字段映射。
- 若连接失败、权限不足、数据为空或字段未知，应显示清晰的诊断信息。
- 不要用硬编码假数据冒充用户真实任务、金币、属性或商店内容。
- 任何新增字段都应有官方依据；无法确认时应保留空状态或隐藏该字段。

### 4. 实现界面与操作

- 默认采用本机运行方式，避免把局域网地址或 Token 放到云端托管环境。
- Token 只能由本地服务端代理读取，不放在浏览器代码、URL、日志或截图里。
- 默认只监听回环地址，除非用户明确需要局域网访问并了解安全风险。
- 把接口返回的任务名、属性名、商品名等外部文本当作不可信数据，使用安全 DOM API 渲染，避免直接拼入 `innerHTML`。
- 写操作必须有明确的用户触发、加载状态、失败提示和业务结果检查。
- 写操作超时或结果不明确时，不要自动重试；先刷新只读数据或让用户确认状态。
- 对破坏性或经济性操作（完成任务、奖励、购买、惩罚等）不要在“诊断”流程中自动执行。

### 4.5 地址切换（所有带页面的界面必做）

自定义界面最容易卡住人的一步是「手机 IP 变了」。因此**任何带页面的示例或 AI 生成的界面，都必须在顶栏提供地址切换**，而不是让人回去改 `config.json`。

必做三件事：
1. 代理暴露 `GET /__upstream`（读当前地址）与 `POST /__upstream`（改地址），**只改内存、不写配置文件**；
2. 顶栏显示当前地址 + 一个输入框 + 一个「换」按钮；
3. 切换成功后自动重新拉取数据，失败时把错误原因显示在页面上。

可粘贴实现（放到 `proxy.js` 的 `/cloud/` 路由之前；启动时把 `UPSTREAM_HOST` / `UPSTREAM_PORT` 改成 `let`）：

```js
const HOST_RE = /^([^:\s/]+)(?::(\d{1,5}))?$/;
// 启动时使用 HOST_RE 校验 config.json，并将 UPSTREAM_HOST / UPSTREAM_PORT 声明为 let。
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
```

前端片段（沿用各示例的样式）：

```js
const box = document.getElementById("upstreamBox");
fetch("/__upstream").then(r => r.json()).then(d => { box.textContent = d.host + ":" + d.port; });
document.getElementById("upstreamBtn").onclick = async () => {
  const r = await fetch("/__upstream", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ host: document.getElementById("upstreamInput").value }) });
  const d = await r.json();
  if (!r.ok) { showErr(d.error || "切换失败"); return; }
  box.textContent = d.host + ":" + d.port;
  document.getElementById("upstreamInput").value = "";
  await load();
};
```

> 安全：该接口仅在回环监听下可用，且不写配置文件——它改变的是本次运行的上游地址，重启即回到 `config.json` 的值。

### 5. 验证并交付

- 运行项目提供的语法检查、配置检查和测试。
- 手动验证首次加载、空数据、连接失败、接口错误、长文本和手机屏幕布局。
- 对写操作验证成功、明确失败、未知结果三种状态。
- 检查控制台没有泄露 Token，且任务名等内容不能触发 HTML 注入。
- 最后提供启动命令、配置方式、已验证的能力、未验证的限制和排错方法。
- 不得声称“已实测”未实际运行的功能；区分静态检查与真实设备联调。

## 可验证的完成判据

只有以下项目有实际证据时，才将对应能力报告为“已验证”；未执行的项目标为“未验证”，不要用静态检查代替真实设备联调。

- [ ] **环境与配置**：已检查所用示例的配置文件存在且格式有效；报告中不输出 Token 或其他秘密。
- [ ] **只读连通性**：实际运行 `node scripts/doctor.js <示例目录>`，并记录命令结果；若未连接真实手机，明确标注。
- [ ] **真实数据读取**：已通过官方只读接口成功取得数据，并核对响应结构；mock 数据或示例占位内容不算真实数据验证。
- [ ] **写操作边界**：未在诊断流程中执行写操作；每个写操作都有明确用户触发和业务级结果检查，未知结果不显示为成功。
- [ ] **重试安全**：完成、放弃、购买、奖励等非幂等操作在超时后不会自动重放。
- [ ] **凭据与输入安全**：Token / API Key 未出现在前端代码、URL、提交记录、日志或截图中；外部文本使用安全 DOM API。
- [ ] **自动化检查**：实际运行适用的语法检查与测试，列出每条命令的真实结果；未运行的测试不得标为通过。
- [ ] **交付说明**：给出启动 / 配置步骤、已验证能力、未验证事项、已知限制和排错路径。

## 交付前检查清单

- [ ] 顶栏有地址显示与切换（`/__upstream`），切换后能重新拉到数据。

- [ ] 官方接口文档和必要时的官方源码已核对。
- [ ] 未自行发明接口路径、参数、字段或版本要求。
- [ ] 真实数据与占位内容有明确区分。
- [ ] 只读诊断不会执行写操作。
- [ ] Token 不在前端、URL、提交记录或日志中。
- [ ] 本地代理默认只允许本机访问。
- [ ] 外部数据通过安全 DOM API 展示。
- [ ] 写操作检查业务级结果，未知结果不会被显示为成功。
- [ ] 写操作没有静默自动重试。
- [ ] 已运行可执行的检查，并如实报告检查范围。

## 可复制给 AI 的开工指令

```text
先读取本项目的 README、docs/custom-ui-ai-mcp.md、docs/ai-build-standard.md 和相关示例。
开始写代码前，必须核对官方云人升 HTTP 文档与人升 URL Scheme 文档；若官方文档说明定义可能滞后，再核对它指向的官方 SDK 源码。接口路径、方法、参数、请求体、响应结构、权限和版本要求都不能靠猜。

先检查现有文件和运行环境，再做最小必要修改。先用只读请求验证连接和真实数据，不要用假数据伪装真实结果。不要在诊断时执行完成任务、奖励、购买、惩罚等写操作。

默认只在本机运行；Token 只放在本地服务端配置，不进入浏览器、URL 或日志。动态文本用安全 DOM API 渲染。写操作必须检查官方定义的业务级结果；如果超时或结果不明确，不要自动重试，也不要谎报成功。

完成后运行可用的测试和语法检查，给出启动步骤、实际验证过的内容、未验证的内容与排错方法。对官方资料未说明的内容，明确标注不确定，不要编造。
```
