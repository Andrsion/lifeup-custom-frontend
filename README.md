# 自定义人升 · 自己做一层界面（含 AI / MCP）

用《人升》(LifeUp) 做游戏化待办，但界面想自己定？这个项目在 App 之外另做一层界面：网页看板、桌面仪表盘、AI 助手或群机器人，任务和金币还是人升里的那一套。本项目是第三方展示与交互层，不是人升官方仓库，也不替代 App 内的业务规则。

**支持范围：只支持《人升》（Android）+ 云人升 HTTP 接口，暂不支持 ulives**——本项目依赖人升提供的本地数据接口，ulives 目前没有对应能力。人升提供这些接口是本项目的技术基础，但不代表本项目已被官方收录或背书。 官方 2026-10-26 在[《开放接口》](https://wiki.lifeupapp.fun/zh-cn/guide/api.md)页写明「由于 MCP 是开放的，你也可以基于它自制客户端（例如做一个自己的网页版）」，并在 FAQ 说明「不做内置 AI，改为引导 MCP + 外部 Agent」——本项目正是这条路的一种做法；官方只是允许自制，并未收录或背书本项目。

> **开始前先确认一件事**：这条路需要《人升》会员（**一次性买断，无订阅**；价格与权益以 App「侧边栏 → 扩展」页为准）。国内版连云人升的下载入口都开在会员区——不是会员，后面一步也走不了。**只想先了解概念、暂时不想花钱的，看到这里就可以停**，读一下 [会员与接口门槛](docs/membership.md) 就够。**10 秒确认自己是不是会员**：打开人升 → 侧边栏 → 设置 → 实验，里面能看到并能下载《云人升》，说明你已经是会员，直接往下走；看不到这个入口，就是还没开通。（价格与权益详情在 App「侧边栏 → 扩展」页，本仓库不写价格。）

两个词先说清楚，后面就不绕了：

- **云人升**：人升的配套组件，在手机上开一个本地服务，这个项目靠它读写你的数据。
- **本地代理**：电脑上的小程序，替网页转发对手机的请求。浏览器通常不允许网页直接读取另一个地址（例如手机 IP）的响应，这种限制叫跨域（CORS）；本地代理让网页先请求电脑，再由电脑访问手机。

（MCP 是什么，等用到时再看最后的「几个词」。）

## 你需要什么

- 一台**电脑**（Windows / macOS）
- 手机与电脑连**同一个 Wi-Fi**
- **Node.js 20+**：后面那个「双击启动」的看板，底层要靠它跑。**你不用手动打开它，装完就不用管了。** 怎么装：去 [nodejs.org](https://nodejs.org/) 点 **LTS**（长期支持版，就是给普通人用的稳定版），下载 Windows / macOS 安装包，一路「下一步」到底。怎么确认装好：开始菜单搜 PowerShell 打开，输入 `node -v`，看到 `v20` 或更高的数字就对了；如果回车后显示 `'node' 不是内部或外部命令`（Windows）或 `command not found`（macOS），说明没装好、或装完还没重开窗口——先关掉 PowerShell 重新打开试一次，仍不行就重装一遍。装好之后你会看到类似 `v22.11.0` 这样的一行。装错不会弄坏电脑，可以随时卸掉重装。官网慢就用国内镜像，见[排错指南](docs/troubleshooting.md)「装 Node / 下依赖很慢」。
- 手机上是**人升 + 云人升**，并开启「读取人升数据」。云人升在应用商店搜不到：国内版要**先有会员**，再在 人升「侧边栏 → 设置 → 实验」里点《云人升》下载（非会员看不到该入口）；Google Play 版也可在商店搜《云人升》（`net.lifeupapp.lifeup.http`）
- **人升会员**（**是硬前提**：国内版连云人升的下载入口都在会员区；调用接口当然也要会员）—— 详见 [会员与接口门槛](docs/membership.md)

**只有手机、没有电脑？** 做不了 —— 自定义界面要在电脑上跑本地代理；MCP 也一样，需要电脑上装 Node.js 并运行客户端。可以先了解概念，有条件时再动手。

## 先选一条路

| 你的目标 | 从这里开始 |
| --- | --- |
| **我想直接运行示例** | 进入 [minimal-html](examples/minimal-html/README.md)（一个单页看板：顶部金币与属性、中间任务列表带「完成」按钮，跑起来就能点），按说明配置并启动；需要大屏时用 [desktop-dashboard](examples/desktop-dashboard/)。 |
| **我想让 AI 帮我做** | **推荐使用本地 Agent**：例如 Cursor / Trae / Claude Code / WorkBuddy。它们可以调用大模型，并在授权范围内读写本地文件、执行命令，适合自动搭建和修改项目。先读 [llms.txt](llms.txt)，再按任务阅读 [实现方案](docs/custom-ui-ai-mcp.md) 与 [AI 施工标准](docs/ai-build-standard.md)；群机器人示例见 [group-bot](examples/group-bot/)。<br><br>**只用网页版 AI（豆包 / Kimi / DeepSeek）同样能做，而且做出来的东西可以和 Agent 一样**——用的是同一个大模型，区别只在「谁动手」：Agent 由 AI 自己读写文件、执行命令；网页版 AI 负责写代码，**你负责把代码存成文件、双击启动**。多几步复制粘贴，不用放弃。<br><br>**具体做法（全程不需要命令行）：**<br>1. 让 AI **完整输出**整个 `index.html`，并明确要求「不要省略、不要用 `…` 代替、不要写『其余同上』」。<br>2. 用记事本把代码粘进去，另存为 **`index.html`**——保存类型选**所有文件**，文件名带 `.html`，编码选 **UTF-8**。扩展名存成 `.txt` 是这一步最常见的翻车点。<br>3. 把文件放进 [minimal-html](examples/minimal-html/README.md) 目录：在解压出来的文件夹里找到 `examples/minimal-html` 这个文件夹，把刚存好的 `index.html` **用鼠标拖进去**，弹出「替换」就点替换；然后**双击 `start.bat`**。双击后会弹出一个黑底窗口——**那是正常的，别关它**，关了页面就打不开；想退出时直接关掉这个窗口即可。<br>4. 打不开或报错，就把报错原文整段贴回给 AI，让它改——这就是「你当手、它当脑」的循环。<br><br>两个已知坑：① 网页版窗口上下文短，一次让它写太大容易断在半句，建议**先跑通最小版再一块块加**；② 它看不到你手机里的清单名和货币叫法，需要你把结构贴给它，或直接用 [世界观 / 主题参考](docs/samples.md) 的换名对照表。环境准备（Node.js、云人升、会员）与 Agent 路线完全相同。 |
| **我只想用 AI 操作人升（MCP）** | 按 [MCP 安装与使用指南](docs/mcp-quickstart.md) 配置客户端；需要了解 Skills 时看 [MCP 与 Skills 指南](docs/mcp-skills.md)，不需要自己开发界面。 |
| **我已经做好了界面，想投稿** | 见下方「[投稿你的界面](#投稿你的界面)」；只投主题 / 换名（不用交代码）也欢迎 |
| **我遇到问题了** | 先运行下面的只读诊断，再查 [排错指南](docs/troubleshooting.md)；接口细节见 [API 速查表](docs/api-cheatsheet.md)。 |

如果你更想使用现成的桌面端应用，而不是自己制作网页界面，也可以了解官方的 [LifeUp-Desktop](https://github.com/Ayagikei/LifeUp-Desktop)；它与本仓库的自定义网页方案是不同路线。

## 文档怎么读

| 难度 | 从这几篇开始 |
| --- | --- |
| 入门 | [会员与接口门槛](docs/membership.md) · [minimal-html 快速上手](examples/minimal-html/README.md) · [排错指南](docs/troubleshooting.md) |
| 参考 | [API 速查表](docs/api-cheatsheet.md) · [世界观 / 主题参考](docs/samples.md) · [从书到人升](docs/books-to-lifeup.md) |
| 进阶 | [实现方案](docs/custom-ui-ai-mcp.md) · [AI 施工标准](docs/ai-build-standard.md) · [MCP 与 Skills 指南](docs/mcp-skills.md) · [MCP 安装与使用指南](docs/mcp-quickstart.md) |
| 主题施工稿 | [docs/specs/](docs/specs/)：星露谷农场 / 原神 / 崩坏：星穹铁道（界面规格 + 可粘贴提示词） |

## 开工前 5 分钟自检

1. **确认手机侧版本与权限**：人升与云人升已装好，并开启「读取人升数据」；具体版本门槛按所用能力不同，见下方「版本门槛」表。
2. **确认网络**：手机与电脑通常需要在同一局域网；确认云人升显示的 IP 和端口，默认端口为 `13276`。
3. **确认运行环境**：本地示例需要 Node.js 20+；没装的话先去 [nodejs.org](https://nodejs.org/) 安装 LTS；AI 工具与 Agent 的要求见上面「先选一条路」。
4. **把仓库弄到电脑上**：在 GitHub 仓库页面点绿色 **Code** → **Download ZIP** → 解压到任意文件夹（记下路径，后面所有命令都在这个文件夹里跑）。
5. **准备本地配置**：进入要运行的示例目录，将 `config.example.json` 复制为 `config.json`，按示例说明填写云人升地址。`host` 就填云人升首页显示的 `IP:13276`（形如 `192.168.1.23:13276`，`config.example.json` 里就是示例样子）。填错也不用怕：格式不对或端口写错，双击 `start.bat` 时会直接用 `✖` 告诉你哪不对，不会静默失败。若云人升启用了 Token，`tokenHeader` 保持为 `Authorization`，`token` 填原始 Token 值（不要加 `Bearer ` 前缀）；Token 不匹配时会返回 HTTP `401`（`Invalid API token`）。不要提交真实配置或 Token.
6. **（可选）先做一次只读诊断**：想确认能不能连上手机再往下走，就用它；**不想碰命令行可以整条跳过**，直接双击 `start.bat` 也能启动，连不上再回来。要跑的话最省事的是双击 `examples/minimal-html/check.bat`（Windows）或 `check.command`（macOS），它会自己找到目录并检查。看到 `✓ 只读检查通过` 就是成功；看到 `✖` 说明没过，按提示改。也可以手动在终端里运行：

   ```bash
   node scripts/doctor.js examples/minimal-html
   ```

   诊断只读取 `GET /info`，不会完成任务、购买或发放奖励。

## 给 AI Agent 的启动指令

将下面的指令和仓库交给你使用的本地 AI Agent。项目文档以 GitHub 仓库 `main` 分支当前内容为准；若通过镜像读取，先确认镜像同步情况。接口事实以对应官方资料为准。

```text
请先读取仓库根目录的 llms.txt，并按任务路由继续读取 docs/ai-build-standard.md、docs/custom-ui-ai-mcp.md 及相关示例。先盘点现有文件与运行环境，再做最小必要修改。

接口路径、方法、参数、请求体、响应字段、权限与版本门槛必须核对对应官方资料，不得臆造。先做只读连通测试，不得用假数据冒充真实用户数据。Token / API Key 不得进入前端、URL、公开仓库或日志。写操作必须由用户明确触发，检查业务级结果；超时或结果不明时不得自动重试。

完成后运行可用的检查和测试，并列出实际执行的命令、通过 / 失败结果、真实设备联调情况及未验证事项。不要声称运行过未实际执行的测试。
我的主题与需求：<可选填写>
我的运行环境：<Windows / macOS / Linux；Node.js 版本；所用本地 Agent>
```

## 直接让 AI 操作人升（MCP）

如果你不需要自定义网页，只想让 AI 查询任务、分析数据或按你的指令操作人升，可以先把下面这句话复制给有权限操作你电脑的 AI Agent：

> 按这份文档帮我安装 LifeUp MCP 并完成首次连接：[https://wiki.lifeupapp.fun/zh-cn/guide/api_mcp.md](https://wiki.lifeupapp.fun/zh-cn/guide/api_mcp.md)

Agent 需要能操作本机 MCP 配置、执行命令并访问手机所在的局域网；它应保留已有 MCP 配置，缺少设备地址或 Token 时先询问你，并通过只读查询验证连接。若无法操作本机或访问局域网，它应说明哪些步骤需要你手动完成。详细步骤与排错见 [MCP 安装与使用指南](docs/mcp-quickstart.md)；Skills 的安装差异和进阶工作流见 [MCP 与 Skills 指南](docs/mcp-skills.md)。

## 版本门槛：按能力分别核对

> 不知道自己的版本？人升在「设置 → 关于」查看；云人升打开 App 首页即可看到版本与 `IP:13276`。

| 能力 | 当前文档口径 |
| --- | --- |
| Cloud HTTP 基础查询 | 官方 Cloud HTTP 文档要求人升 v1.91+ 与最新版云人升；具体路由、字段和权限仍以对应文档为准。 |
| HTTP 特定字段 / 能力 | 逐项核对版本要求。例如 `weekdays` 标注人升 v1.106.0+；这不是所有 HTTP 路由的统一门槛。 |
| URL Scheme | 方法名、参数与个别方法的版本要求以[官方 API 文档](https://wiki.lifeupapp.fun/zh-cn/guide/api.md)对应条目为准，不把它与 HTTP 版本要求混用。 |
| MCP 接入 | 按[官方 MCP 文档](https://wiki.lifeupapp.fun/zh-cn/guide/api_mcp.md)检查客户端接入要求；该 Wiki 页面目前写云人升 3.0.0+。 |
| 当前 Skills 工作流 | 当前官方 `lifeup-cloud` Skill 要求人升 v1.106.0+、云人升 3.0.1+。如需完整当前 Skills 工作流，按更具体的 Skill 要求使用 3.0.1+；这不是所有 HTTP 路由的统一门槛。 |

权威资料入口和冲突处理规则见 [llms.txt](llms.txt#权威来源与分工)。若官方文档提示定义可能滞后，再核对它指向的官方 SDK 实现；无法确认时应明确标注不确定，不得猜测。

## 几个词

只用到一个词：**MCP** —— 一种让 AI 工具直接操作人升的标准接口，不用自己写界面。

## 投稿你的界面

做了一套自己的界面？三种投法，从轻到重：
1. **只投主题 / 换名**（不交代码）：提 [Issue「主题 / 换名 投稿」](https://github.com/Andrsion/lifeup-custom-frontend/issues/new/choose)，写清「金币→？任务→？属性→？」即可，会收进 [世界观 / 主题参考](docs/samples.md)。
2. **投可运行的界面**（html / 示例）：先跑 `python3 scripts/case_check.py <你的文件或目录>` 确认没有 ✖（常见是夹带了自己的 token 或手机 IP），再按 [社区界面案例](docs/cases/) 的三步提交。
3. **投施工稿**（完整规格 + 提示词）：同类走 Issue，说明所属主题与机制轴。

不想碰 Git？在频道 / 群里发帖带截图，注明「可投稿」，管理员会替你整理提交。投稿通过后会：收录进 [docs/cases/](docs/cases/)（或 samples.md）、在 CHANGELOG 记一条，并注明作者。

## 仓库维护

- `node scripts/doctor.js <示例目录>`：检查本地配置并只读请求 `GET /info`，例如 `node scripts/doctor.js examples/minimal-html`。
- `node scripts/test_proxy.js`：运行本地代理集成测试，使用 mock 上游，不会访问真实手机。
- `python3 scripts/check_repo.py`：检查配置、脚本语法、本地 Markdown 链接和 `llms-full.txt` 生成稳定性。
- `python3 scripts/case_check.py <html|目录>`：投稿前的脱敏与可跑性检查，`--emit` 可生成案例骨架。
- `llms-full.txt` 是生成文件；修改源文档后由 `scripts/build_llms.py` 重建，不要手工编辑。

本仓库为社区整理的公开项目，非 LifeUp 官方仓库。许可信息见 [LICENSE](LICENSE)。
