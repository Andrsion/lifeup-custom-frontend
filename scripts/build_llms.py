#!/usr/bin/env python3
"""从仓库文档自动重建 llms-full.txt。

默认收录 README.md 与 docs/ 下的 Markdown 文档；docs/specs/ 保持为可选的
单主题材料，不并入总文档。新增或重命名普通文档无需修改本脚本。

用法：在仓库根目录执行 `python3 scripts/build_llms.py`
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
DOCS = ROOT / "docs"
EXCLUDED_DIRS = {"specs"}
EXCLUDE_MARKER = "<!-- llms:exclude -->"

# README 置顶，项目主文档紧随其后；其余文档按路径稳定排序。
SOURCE_PRIORITY = {
    "README.md": 0,
    "docs/custom-ui-ai-mcp.md": 1,
}

# 为现有核心文档保留更易读的章节标题；新增文档默认使用相对路径。
SECTION_NAMES = {
    "README.md": "README",
    "docs/custom-ui-ai-mcp.md": "实现方案",
    "docs/mcp-skills.md": "MCP 与 Skills 指南",
    "docs/api-cheatsheet.md": "接口速查表",
    "docs/troubleshooting.md": "排错 · 常见坑",
    "docs/books-to-lifeup.md": "从书到人升",
    "docs/samples.md": "世界观 / 主题参考",
    "docs/earth-online-glossary.md": "地球 Online 梗词表",
    "docs/ai-build-standard.md": "AI 施工标准",
    "docs/mcp-quickstart.md": "MCP 安装与使用指南",
    "docs/theme-spec-template.md": "主题规格模板",
}

HEADER_TEMPLATE = """# 自定义人升 · 核心文档（llms-full.txt）

> 本文件由 `scripts/build_llms.py` 从仓库各源文档**自动生成**，请勿手改。
> 修改内容请改源文件，然后重跑：`python3 scripts/build_llms.py`
> 自动收录 `README.md` 与 `docs/` 下的 Markdown 文档；`docs/specs/` 是可选的单主题材料，不并入本文件，索引见 `llms.txt`。
> 以 `_` 开头的文件或目录，以及包含 `<!-- llms:exclude -->` 标记的文档会被跳过。文件开头自动生成收录目录。
> 本文档体量：{stats}（正文口径，由脚本统计，随每次重建更新）。
> 使用建议：此文档较大，token 受限时不要整篇投喂，改用 llms.txt 的路由逐篇读取。

"""


def should_exclude(path: Path) -> bool:
    """排除下划线前缀路径、可选 specs 目录和带显式排除标记的文档。"""
    relative_parts = path.relative_to(ROOT).parts
    if any(part.startswith("_") for part in relative_parts):
        return True
    if any(part in EXCLUDED_DIRS for part in path.relative_to(DOCS).parts[:-1]) if path != README else False:
        return True
    return EXCLUDE_MARKER in path.read_text(encoding="utf-8")


def discover_sources() -> list[Path]:
    """README 与 docs/**/*.md 自动发现；README 置顶，主文档随后，其余稳定排序。"""
    if not README.is_file():
        raise SystemExit("缺少源文件：README.md")
    if not DOCS.is_dir():
        raise SystemExit("缺少源目录：docs/")

    candidates = [README, *DOCS.rglob("*.md")]
    sources = [
        path for path in candidates
        if path.is_file() and not should_exclude(path)
    ]
    return sorted(
        sources,
        key=lambda path: (
            SOURCE_PRIORITY.get(path.relative_to(ROOT).as_posix(), 2),
            path.relative_to(ROOT).as_posix().casefold(),
        ),
    )


def main() -> None:
    sources = discover_sources()
    parts = ["## 文档目录（自动生成）\n\n"]
    for path in sources:
        rel = path.relative_to(ROOT).as_posix()
        name = SECTION_NAMES.get(rel, rel)
        # Stable source paths remain useful even if display titles change.
        parts.append(f"- **{name}** — {rel}" + chr(10))
    parts.append("\n> 目录用于快速定位章节；各章节下方的源路径标记是稳定标识。\n\n")

    for path in sources:
        rel = path.relative_to(ROOT).as_posix()
        name = SECTION_NAMES.get(rel, rel)
        body = path.read_text(encoding="utf-8").strip()
        parts.append(f"<!-- ===== {name} ({rel}) ===== -->\n\n{body}\n\n")

    body = "".join(parts)
    stats = f"{len(body)} 字符 · {len(sources)} 篇"
    output = (HEADER_TEMPLATE.format(stats=stats) + body).rstrip() + "\n"
    out = ROOT / "llms-full.txt"
    out.write_text(output, encoding="utf-8")
    print(
        f"已生成 {out.name}：{len(output.encode('utf-8'))} 字节 / "
        f"{output.count(chr(10))} 行 / {len(sources)} 个文档"
    )
    print(f"体量：{stats}")

if __name__ == "__main__":
    main()
