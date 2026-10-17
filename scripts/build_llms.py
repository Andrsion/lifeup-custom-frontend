#!/usr/bin/env python3
"""从仓库各源文档重建 llms-full.txt。自动生成，勿手改 llms-full.txt 本身。

用法：在仓库根目录执行 `python3 scripts/build_llms.py`
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 拼接顺序即本列表顺序；新增/改名文档时改这里
SOURCES = [
    ("README", "README.md"),
    ("实现方案", "docs/custom-ui-ai-mcp.md"),
    ("接口速查表", "docs/api-cheatsheet.md"),
    ("排错 · 常见坑", "docs/troubleshooting.md"),
    ("从书到人升", "docs/books-to-lifeup.md"),
    ("世界观 / 主题参考", "docs/samples.md"),
    ("地球 Online 梗词表", "docs/earth-online-glossary.md"),
]

HEADER = """# 自定义人升 · 核心文档（llms-full.txt）

> 本文件由 `scripts/build_llms.py` 从仓库各源文档**自动生成**，请勿手改。
> 修改内容请改源文件，然后重跑：`python3 scripts/build_llms.py`
> 主题施工稿（`docs/specs/`）是可选的单主题材料，不并入本文件，索引见 `llms.txt`。

"""


def main() -> None:
    parts = [HEADER]
    for name, rel in SOURCES:
        path = ROOT / rel
        if not path.exists():
            raise SystemExit(f"缺少源文件：{rel}")
        body = path.read_text(encoding="utf-8").strip()
        parts.append(f"<!-- ===== {name} ({rel}) ===== -->\n\n{body}\n\n")

    text = "".join(parts).rstrip() + "\n"
    out = ROOT / "llms-full.txt"
    out.write_text(text, encoding="utf-8")
    print(
        f"已生成 {out.name}：{len(text.encode('utf-8'))} 字节 / "
        f"{text.count(chr(10))} 行"
    )


if __name__ == "__main__":
    main()
