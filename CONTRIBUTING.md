# 贡献指南

本仓库是社区整理的**公开资料 + 可运行示例**，欢迎补充。

## 可以贡献什么

- 🎨 **主题 / 世界观**：新的 IP、社区体系、换名对照表 → 改 [docs/samples.md](docs/samples.md) 或提 Issue
- 🧰 **示例**：新的示例（不同框架 / 大屏 / 机器人 / 语音）→ 放 `examples/` 下，自成一个可跑的小项目
- 📖 **从书到人升**：把你的读书笔记也翻译成「在人升上的用法」→ 改 [docs/books-to-lifeup.md](docs/books-to-lifeup.md)
- 🐞 **勘误**：接口 / 参数 / 链接写错了 → 提 Issue 或 PR
- 🎨 **主题 / 换名**：提 Issue「主题 / 换名 投稿」→ 收录进 [docs/samples.md](docs/samples.md)

## 提交前

- 接口一律**以官方为准**：<https://wiki.lifeupapp.fun/zh-cn/guide/api_cloud.md>；**不要写没有依据的参数**。
- 示例要**能跑**：只依赖 **Node.js 20+**，尽量零依赖；双击即可启动。
- **不要提交**任何账号 / Token / 你的手机 IP —— 示例里用 `config.example.json` 占位。\n- 涉及接口的修改必须对照 [官方云人升文档](https://wiki.lifeupapp.fun/zh-cn/guide/api_cloud.md) 与 [官方 URL Scheme 文档](https://wiki.lifeupapp.fun/zh-cn/guide/api.md)；若官方 Wiki 提示定义可能滞后，再核对其指向的官方 SDK 源码。\n- 新主题优先使用 [主题规格模板](docs/theme-spec-template.md)；AI 生成代码遵循 [AI 施工标准](docs/ai-build-standard.md)。\n- 提交前可运行 `python scripts/check_repo.py`，确认配置、脚本语法和本地 Markdown 链接检查通过。
- 文件命名：文档用 `kebab-case.md`。

## 分支与 PR

- 主分支是 **`main`**（写成 `master` 会 404）。
- 说明「改了什么、为什么」；示例请附一张截图或一段命令输出。
