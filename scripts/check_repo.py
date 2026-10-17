#!/usr/bin/env python3
"""轻量仓库质量检查：链接、示例配置、JS 语法与 llms 生成确定性。"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NODE_FILES = [
    ROOT / "examples/minimal-html/proxy.js",
    ROOT / "examples/desktop-dashboard/proxy.js",
    ROOT / "examples/group-bot/bot.js",
    ROOT / "scripts/doctor.js",
    ROOT / "scripts/test_proxy.js",
]
MARKDOWN_LINK = re.compile(r"!??\[[^\]]*\]\(([^)]+)\)")


def check_json() -> list[str]:
    errors: list[str] = []
    for path in sorted((ROOT / "examples").rglob("config.example.json")):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: JSON 无效：{exc}")
    return errors


def check_javascript() -> list[str]:
    errors: list[str] = []
    for path in NODE_FILES:
        result = subprocess.run(
            ["node", "--check", str(path)],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            errors.append(f"{path.relative_to(ROOT)}: Node.js 语法检查失败\n{result.stderr}")
    # 检查两个 HTML 中的内嵌脚本，避免只检查代理而漏掉前端脚本。
    for html in sorted((ROOT / "examples").rglob("index.html")):
        content = html.read_text(encoding="utf-8")
        if "innerHTML" in content or "insertAdjacentHTML" in content:
            errors.append(f"{html.relative_to(ROOT)}: 动态数据渲染不得使用 innerHTML / insertAdjacentHTML")
        if not re.search(r"api_result\s*!==\s*true", content):
            errors.append(f"{html.relative_to(ROOT)}: 写操作必须明确检查官方业务结果")
        scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script\s*>", content, re.I | re.S)
        for index, script in enumerate(scripts):
            with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
                handle.write(script)
                temp_path = Path(handle.name)
            try:
                result = subprocess.run(["node", "--check", str(temp_path)], text=True, capture_output=True)
                if result.returncode:
                    errors.append(f"{html.relative_to(ROOT)} 内嵌脚本 #{index + 1} 语法检查失败\n{result.stderr}")
            finally:
                temp_path.unlink(missing_ok=True)
    return errors


def check_local_links() -> list[str]:
    errors: list[str] = []
    markdown_files = [ROOT / "README.md", ROOT / "CONTRIBUTING.md", ROOT / "CHANGELOG.md"]
    markdown_files += list((ROOT / "docs").rglob("*.md"))
    markdown_files += list((ROOT / "examples").rglob("*.md"))
    for source in markdown_files:
        if not source.is_file():
            continue
        text = source.read_text(encoding="utf-8")
        for raw_target in MARKDOWN_LINK.findall(text):
            target = raw_target.strip().strip("<>")
            if not target or target.startswith(("https://", "http://", "mailto:", "data:", "#")):
                continue
            target = target.split("#", 1)[0].split("?", 1)[0]
            if not target:
                continue
            resolved = (source.parent / target).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                errors.append(f"{source.relative_to(ROOT)}: 本地链接越出仓库：{raw_target}")
                continue
            if not resolved.exists():
                errors.append(f"{source.relative_to(ROOT)}: 本地链接目标不存在：{raw_target}")
    return errors


def check_llms_deterministic() -> list[str]:
    script = ROOT / "scripts/build_llms.py"
    output = ROOT / "llms-full.txt"
    if not script.exists() or not output.exists():
        return ["缺少 scripts/build_llms.py 或 llms-full.txt"]
    before = output.read_bytes()
    first = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    if first.returncode:
        return [f"生成 llms-full.txt 失败：{first.stderr}"]
    generated_once = output.read_bytes()
    second = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    if second.returncode:
        return [f"第二次生成 llms-full.txt 失败：{second.stderr}"]
    generated_twice = output.read_bytes()
    if generated_once != generated_twice:
        return ["llms-full.txt 生成结果不稳定"]
    # 保留原文件对比供 CI 输出提示；构建工作流负责在源文档更新后提交生成结果。
    if before != generated_once:
        print("提示：llms-full.txt 与源文档不同步；build-llms-full 工作流会重建该文件。")
    content = generated_once.decode("utf-8")
    if "<!-- ===== README (README.md) ===== -->" not in content:
        return ["llms-full.txt 缺少 README 主章节"]
    if content.find("<!-- ===== README (README.md) ===== -->") > content.find("<!-- ===== 实现方案 (docs/custom-ui-ai-mcp.md) ===== -->"):
        return ["llms-full.txt 的主文档排序不正确"]
    if "<!-- ===== docs/specs/" in content:
        return ["llms-full.txt 不应收录 docs/specs/ 可选主题文档"]
    return []


def main() -> int:
    errors = []
    errors += check_json()
    errors += check_javascript()
    errors += check_local_links()
    errors += check_llms_deterministic()
    if errors:
        print("仓库质量检查失败：")
        for error in errors:
            print(f"\n- {error}")
        return 1
    print("✓ JSON 配置、Node.js/内嵌脚本语法、本地 Markdown 链接、llms-full.txt 确定性检查均通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
