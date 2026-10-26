# 贡献指南

本仓库是社区整理的**公开资料 + 可运行示例**，欢迎补充。

## 可以贡献什么

- 🎨 **主题 / 世界观**：新的 IP、社区体系、换名对照表 → 改 [docs/samples.md](docs/samples.md) 或提 Issue
- 🧰 **示例**：新的示例（不同框架 / 大屏 / 机器人 / 语音）→ 放 `examples/` 下，自成一个可跑的小项目
- 📖 **从书到人升**：把你的读书笔记也翻译成「在人升上的用法」→ 改 [docs/books-to-lifeup.md](docs/books-to-lifeup.md)
- 🐞 **勘误**：接口 / 参数 / 链接写错了 → 提 Issue 或 PR
- 🎨 **主题 / 换名**：提 Issue「主题 / 换名 投稿」→ 收录进 [docs/samples.md](docs/samples.md)

## 投稿一套界面

**不需要 Git 或电脑：** 在手机打开[完整界面案例投稿表单](https://github.com/Andrsion/lifeup-custom-frontend/issues/new?template=full-case-submission.yml)，填写说明，上传 ZIP 或粘贴单页 HTML。GitHub Actions 会自动进行静态脱敏检查并回帖；检查不会执行投稿代码，也不会自动收录。

使用传统文件流程时，完整步骤见 **[docs/cases/README.md](docs/cases/README.md)**。三步概括：

1. `python3 scripts/case_check.py <路径>` 确认没有 ✖（脱敏）；
2. `--emit --slug <小写英文短名>` 生成骨架，填完三处待填；
3. 提 [Issue](https://github.com/Andrsion/lifeup-custom-frontend/issues/new/choose) 或 PR。

只投主题 / 换名（不交代码）的，直接提「主题 / 换名 投稿」Issue 即可.

## 维护者：把投稿导入成案例

1. 打开投稿 Issue，确认内容、授权与素材版权没问题。
2. 去 **Actions → import-case → Run workflow**，填 Issue 编号与 slug，先 `dry_run = true` 跑一遍看报告。
3. 报告无 RED 后再用 `dry_run = false` 跑一次，仓库会自动生成 `docs/cases/<slug>.md`、补索引与 CHANGELOG 并提交。
4. 打开生成文件，补齐三处待填（为什么好玩 / 灵感来源 / 机制决定情绪），必要时调整措辞后提交。

> 自动检查只做静态扫描，不执行投稿代码；工作流只有手动触发才有写权限。
## 提交前

- 接口一律**以官方为准**：<https://wiki.lifeupapp.fun/zh-cn/guide/api_cloud.md>；**不要写没有依据的参数**。
- 示例要**能跑**：只依赖 **Node.js 20+**，尽量零依赖；双击即可启动。
- **不要提交**任何账号 / Token / 你的手机 IP —— 示例里用 `config.example.json` 占位。
- 涉及接口的修改必须对照 [官方云人升文档](https://wiki.lifeupapp.fun/zh-cn/guide/api_cloud.md) 与 [官方 URL Scheme 文档](https://wiki.lifeupapp.fun/zh-cn/guide/api.md)；若官方 Wiki 提示定义可能滞后，再核对其指向的官方 SDK 源码。
- 新主题优先使用 [主题规格模板](docs/theme-spec-template.md)；AI 生成代码遵循 [AI 施工标准](docs/ai-build-standard.md)。
- 提交前可运行 `python scripts/check_repo.py`，确认配置、脚本语法和本地 Markdown 链接检查通过。
- 文件命名：文档用 `kebab-case.md`。

> **什么时候该更新 CHANGELOG**：只有用户能感知到的变化才写——新增文档、修改口径、改流程、修安全问题、加功能。纯重构、排版、机器重建、CI 调整不写。写法是按主题一句话概括一组改动，不要按 commit 逐条罗列。本仓库按日期分节、最新在前，同一天合并为一节，不打 tag / Release。

## 分支与 PR

- 主分支是 **`main`**（写成 `master` 会 404）。
- 说明「改了什么、为什么」；示例请附一张截图或一段命令输出。

## 文档收录约定

`llms-full.txt` 由 `scripts/build_llms.py` 自动生成，收录规则按位置：

- 根目录 `README.md`：收录，固定第一
- `docs/**/*.md`：自动收录（主文档 `docs/custom-ui-ai-mcp.md` 排第二）
- `docs/specs/`：不收录（可选主题材料，单独在 `docs/specs/README.md` 索引）
- 文件或目录以 `_` 开头：不收录
- 正文含 `<!-- llms:exclude -->`：不收录

新增普通文档只需放进 `docs/`，不必改脚本；改完运行 `python3 scripts/build_llms.py`（CI 也会自动重建）。
