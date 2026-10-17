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
EXCLUDED_DIRS = { "specs" }

# 为现有核心文档保留更易读的章节标题；新增文档默认使用相对路径。
SECTION_NAMES = {
    "README.md": "README",
    "docs/custom-ui-ai-mcp.md": "实现方案",
    "docs/api-cheatsheet.md": "接口速查表",
    "docs/troubleshooting.md": "排错 · 常见坑",
    "docs/books-to-lifeup.md": "从书到人升",
    "docs/samples.md": "世界观 / 主题参考",
    "docs/earth-online-glossary.md": "地球 Online 梗词表",
}

HEADER = """# 自定义人升 · 核心文档（llms-full.txt）

> 本文件由 `scripts/build_llms.py` 从仓库各源文档**自动生成**，请勿手改。
> 修改内容请改源文件，然后重跑：`python3 scripts/build_llms.py`
> 自动收录 `README.md` 与 `docs/` 下的 Markdown 文档；`docs/specs/` 是可选的单主题材料，不并入本文件，索引见 `llms.txt`。

"""


def discover_sources() -> list[Path]:
    """README 固定置顶，其余 docs/**/*.md 按路径稳定排序，排除 docs/specs/。"""
    if not README.is_file():
        raise SystemExit("缺少源文件：README.md")
    if not DOCS.is_dir():
        raise SystemExit("缺少源目录：docs/")

    docs = sorted(
        (
            path for path in DOCS.rglob("*.md")
            if path.is_file()
            and not any(part in EXCLUDED_DIRS for part in path.relative_to(DOCS).parts[:-1])
        ),
        key=lambda path: path.relative_to(ROOT).as_posix().casefold(),
    )
    return [README, *docs]


def main() -> None:
    parts = [HEADER]
    for path in discover_sources():
        rel = path.relative_to(ROOT).as_posix()
        name = SECTION_NAMES.get(rel, rel)
        body = path.read_text(encoding="utf-8").strip()
        parts.append(f"<!-- ===== {name} ({rel}) ===== -->\n\n{body}\n\n")

    output = "".join(parts).rstrip() + "\n"
    out = ROOT / "llms-full.txt"
    out.write_text(output, encoding="utf-8")
    print(
        f"已生成 {out.name}：{len(output.encode('utf-8'))} 字节 / "
        f"{output.count(chr(10))} 行 / {len(parts) - 1} 个文档"
    )


if __name__ == "__main__":
    main()
