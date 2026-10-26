#!/usr/bin/env python3
"""Fetch and statically scan a case ZIP or pasted HTML from a GitHub Issue body.

Never executes submitted code. Writes a Markdown report to case-submission-report.md.
"""
from __future__ import annotations

import os
import re
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts" / "case_check.py"
REPORT = ROOT / "case-submission-report.md"
MAX_DOWNLOAD = 25 * 1024 * 1024
MAX_UNPACKED = 50 * 1024 * 1024
MAX_MEMBERS = 1000
ATTACHMENT_RE = re.compile(r"https://github\.com/user-attachments/files/[^\s)>]+", re.I)
FENCE = chr(96) * 3
HTML_BLOCK_RE = re.compile(
    r"###\s+HTML 源码（可选）\s*\n+\s*" + re.escape(FENCE) +
    r"html\s*\n(.*?)\n\s*" + re.escape(FENCE),
    re.I | re.S,
)


def write_report(text: str) -> None:
    REPORT.write_text(text.rstrip() + "\n", encoding="utf-8")
    print(text)


def find_zip_url(body: str) -> str | None:
    for raw in ATTACHMENT_RE.findall(body):
        candidate = raw.rstrip(".,;")
        parsed = urllib.parse.urlparse(candidate)
        if parsed.hostname != "github.com" or not parsed.path.startswith("/user-attachments/files/"):
            continue
        if parsed.path.lower().endswith(".zip"):
            return candidate
    return None


def download_zip(url: str, destination: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "lifeup-custom-frontend-case-check/1.0"},
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        final = urllib.parse.urlparse(response.geturl())
        if final.hostname != "github.com" and not (final.hostname or "").endswith(".githubusercontent.com"):
            raise ValueError("附件下载被重定向到不受支持的主机，已停止检查。")
        data = response.read(MAX_DOWNLOAD + 1)
    if len(data) > MAX_DOWNLOAD:
        raise ValueError("ZIP 下载内容超过 25 MB，已停止检查。")
    destination.write_bytes(data)


def safe_extract(archive_path: Path, destination: Path) -> None:
    total = 0
    with zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        if len(members) > MAX_MEMBERS:
            raise ValueError(f"ZIP 内文件数量超过 {MAX_MEMBERS}，已停止检查。")
        for member in members:
            name = member.filename.replace("\\", "/")
            path = PurePosixPath(name)
            mode = member.external_attr >> 16
            if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
                raise ValueError(f"ZIP 包含不安全路径：{member.filename}")
            if stat.S_ISLNK(mode):
                raise ValueError(f"ZIP 包含符号链接：{member.filename}")
            total += member.file_size
            if total > MAX_UNPACKED:
                raise ValueError("ZIP 解压后超过 50 MB，已停止检查。")
            if member.is_dir():
                continue
            target = destination.joinpath(*path.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, target.open("wb") as output:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)


def run_static_check(target: Path) -> tuple[str, int]:
    result = subprocess.run(
        [sys.executable, str(CHECKER), str(target), "--no-emit"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    output = (result.stdout + "\n" + result.stderr).strip()
    return output, result.returncode


def main() -> int:
    body = os.environ.get("ISSUE_BODY", "")
    with tempfile.TemporaryDirectory(prefix="lifeup-case-check-") as temp:
        tempdir = Path(temp)
        zip_url = find_zip_url(body)
        try:
            if zip_url:
                archive_path = tempdir / "submission.zip"
                download_zip(zip_url, archive_path)
                target = tempdir / "unpacked"
                target.mkdir()
                safe_extract(archive_path, target)
                source_description = "从投稿 Issue 的 ZIP 附件中提取文件"
            else:
                match = HTML_BLOCK_RE.search(body)
                if not match or not match.group(1).strip():
                    write_report(
                        "## 自动脱敏检查：未能检查\n\n"
                        "没有检测到 ZIP 附件或 HTML 源码。请编辑这条 Issue，上传 ZIP 案例包，"
                        "或把完整 HTML 粘贴到「HTML 源码」字段后重新保存。\n\n"
                        "本次未扫描任何代码；这不代表投稿通过。"
                    )
                    return 0
                target = tempdir / "pasted"
                target.mkdir()
                (target / "index.html").write_text(match.group(1), encoding="utf-8")
                source_description = "从投稿表单中的 HTML 源码字段读取"

            output, code = run_static_check(target)
            red = bool(re.search(r"(?:✖ RED|\bRED\b)", output))
            conclusion_match = re.search(r"结论：([^\n]+)", output)
            conclusion = conclusion_match.group(1).strip() if conclusion_match else (
                "不可提交" if code else "需人工复核"
            )
            status = "发现需处理的 RED 项" if red or code else (
                "可提交，仍需人工审核" if conclusion == "可提交" else conclusion
            )
            report = (
                "## 自动脱敏检查结果\n\n"
                f"- 检查来源：{source_description}\n"
                f"- 机器结论：**{status}**\n"
                "- 检查方式：静态扫描；没有执行投稿代码。\n"
                "- 注意：检查通过不等于正式收录，外部资源、运行效果与授权仍需维护者审核。\n\n"
                "<details>\n<summary>查看检查明细</summary>\n\n"
                "~~~text\n" + (output[:12000] or "检查器未返回明细") +
                "\n~~~\n</details>\n"
            )
            write_report(report)
        except (OSError, ValueError, zipfile.BadZipFile, urllib.error.URLError, TimeoutError, subprocess.TimeoutExpired) as exc:
            write_report(
                "## 自动脱敏检查：未完成\n\n"
                f"检查器无法安全读取投稿文件：{type(exc).__name__}: {exc}\n\n"
                "请确认 ZIP 文件完整、文件路径正常，并编辑 Issue 重新提交。此结果不代表投稿通过。"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
