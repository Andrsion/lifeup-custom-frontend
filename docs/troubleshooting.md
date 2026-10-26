# 排错 · 常见坑

> 接口细节以官方为准：<https://wiki.lifeupapp.fun/zh-cn/guide/api_cloud.md>。本页只列**实践中高频踩的坑**。

## 连不上 / 请求超时

- **列表为空 / 请求失败** → 先查云人升「配置」三项：读取「人升」数据权限、悬浮窗权限（Android 10+）、忽略电池优化；再确认人升在后台运行、手机没被厂商省电策略清掉。
- 手机与电脑必须连**同一个 Wi-Fi**；路由器开了 **AP 隔离（客户端隔离）** 会失败 → 关掉它或换网段。
- 先用 **`GET /info`** 做连通自测，通了再谈别的。
- 手机 IP 由 DHCP 分配、**会变** → 建议在路由器给手机**固定 IP**，或每次重查 IP。

## 只有 iPad / 平板当看板

- iPad 可以用 Safari 显示网页，但 **iPadOS 不属于本项目支持的本地 Node.js 代理运行环境**；终端类 App 即使能运行部分命令，也不能保证代理在后台长期运行。
- 云人升是运行在人升 Android 端的配套服务，iPad 本身不能替代 Android 手机提供这组数据接口。
- 推荐把代理运行在常开电脑、NAS 或树莓派等设备上，再让 iPad 访问该设备的看板地址。
- **安全边界**：示例代理默认绑定 `127.0.0.1`，并校验请求的 Host / Origin；因此局域网设备不能直接访问。若要开放给 iPad，必须同时修改监听地址与访问校验，并增加认证和局域网访问限制。不要只改监听地址，也不要把代理端口直接暴露到公网；代理能够转发读写请求，开放访问意味着其他可达设备可能操作你的任务数据。

## Token 认证失败

- 云人升启用了 Token 时，请在配置中使用 `"tokenHeader": "Authorization"`，并将原始 Token 值填入 `"token"`；不要添加 `Bearer ` 前缀。
- Token 不匹配时，官方服务返回 HTTP `401`，响应提示为 `Invalid API token`。这属于 HTTP 认证层，不是 JSON 业务 `code`。
- 先确认 Token 与云人升设置逐字一致；未启用 Token 时保持 `"token": ""`。不要将 Token 放在前端页面、URL、公开仓库或日志中。

## 浏览器直连被 CORS 拦

- 浏览器**直接**请求云人升会被跨域拦截（且 Token 会暴露）→ **必须加一层本地代理**，前端只连 `http://localhost:xxxx`。
- 开发阶段可用 **Vite 的 `server.proxy`**；做成成品就用本仓库示例里的 `proxy.js`。

## 写操作「明明成功却没生效」或「重复扣了」

- 写操作**不幂等**：`complete` / `give_up` / `reward` 等超时后**不要自动重试**。
- `/api/contentprovider` 的顶层 `code=200` **只代表送达**；业务成败要读 **`data[].result.api_result`**。

## 任务「消失」/ 状态错乱

- 任务的 **`id` 每个周期会变**；跨周期识别请用 **`gid`**（恒定不变）。
- 本地缓存请以 **`gid`** 为键，而不是 `id`。

## 为什么不能用「云端生成 + 云端托管」平台

- **秒哒 / Bolt.new / v0 / Lovable** 等：它们跑在云上，**访问不到你家局域网里的手机**，在线预览也绕不开跨域。
- 必须选**在你电脑本地运行**的 AI 工具（Trae / 通义灵码 / CodeBuddy / WorkBuddy / Cursor 等）。

## 版本不够

- 官方云人升 HTTP 文档列出的基础要求为人升 v1.91+ 与最新版云人升；特定字段 / 功能可能要求更高版本。使用前请求 `GET /info`，并按所用功能核对官方文档 / SDK。
- `weekdays`（按每周几重复）字段由官方 HTTP 文档标注为人升 v1.106.0+；这不是全部 HTTP 路由的统一最低版本。

## 装 Node / 下依赖很慢

**Node.js 安装包**（官网慢时用国内同源镜像）

| 镜像 | 地址 |
| --- | --- |
| 阿里云（推荐） | [https://mirrors.aliyun.com/nodejs-release/](https://mirrors.aliyun.com/nodejs-release/) |
| 清华 TUNA | [https://mirrors.tuna.tsinghua.edu.cn/nodejs-release/](https://mirrors.tuna.tsinghua.edu.cn/nodejs-release/) |

进入对应镜像后选版本目录（如 `v20.x.x/`），再下载对应系统的安装包（Windows `.msi` / macOS `.pkg`）。

**npm 依赖**（只有安装 MCP 等需要 `npx` 拉包的场景会用到；本项目示例是零依赖）

```bash
npm config set registry https://registry.npmmirror.com
npm config get registry
```

验证：第二条命令返回 `https://registry.npmmirror.com/` 即成功。

旧的 `registry.npm.taobao.org` 已失效，请使用新的 `registry.npmmirror.com`。

## 仍然搞不定？

带上这些信息去求助，效率最高：`GET /info` 的返回、浏览器控制台报错、你请求的完整 URL 与返回体。
详细求助模板见知识库《🛟 社区求助与反馈指南》。
