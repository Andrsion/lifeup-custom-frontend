#!/usr/bin/env python3
"""Fetch and statically scan a case ZIP or pasted HTML from a GitHub Issue body.

Never executes submitted code. Writes a Markdown report to case-submission-report.md.
"""
from __future__ import annotations

import json
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
    candidates: list[str] = []
    for raw in ATTACHMENT_RE.findall(body):
        candidate = raw.rstrip(".,;")
        parsed = urllib.parse.urlparse(candidate)
        if parsed.hostname != "github.com" or not parsed.path.startswith("/user-attachments/files/"):
            continue
        if parsed.path.lower().endswith(".zip"):
            candidates.append(candidate)
    # If the submitter edits the Issue and uploads a replacement, prefer the newest link.
    return candidates[-1] if candidates else None


def is_allowed_attachment_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and (
        host in {"github.com", "githubusercontent.com"}
        or host.endswith(".githubusercontent.com")
    )


class SafeAttachmentRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not is_allowed_attachment_url(newurl):
            raise ValueError("附件下载重定向到不受支持的主机，已停止请求。")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download_zip(url: str, destination: Path) -> None:
    if not is_allowed_attachment_url(url):
        raise ValueError("附件地址不是受支持的 HTTPS GitHub 附件主机。")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "lifeup-custom-frontend-case-check/1.0"},
    )
    opener = urllib.request.build_opener(SafeAttachmentRedirectHandler())
    with opener.open(request, timeout=25) as response:
        if not is_allowed_attachment_url(response.geturl()):
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


def find_checkable_files(target: Path) -> list[Path]:
    """Return supported static-scan source files; screenshots are not source code."""
    return sorted(
        (path for path in target.rglob("*")
         if path.is_file() and path.suffix.lower() in {".html", ".js", ".css", ".json"}),
        key=lambda path: str(path).casefold(),
    )


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


def parse_submission_fields(body: str) -> dict[str, str]:
    headings = list(re.finditer(r"(?m)^###\s+(.+?)\s*$", body))
    sections = {}
    for index, match in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(body)
        sections[match.group(1).strip()] = body[match.end():end].strip()
    def field(*names: str) -> str:
        value = next((sections[name] for name in names if name in sections), "")
        value = re.sub(r"^<!--.*?-->\s*", "", value, flags=re.S).strip()
        if value.lower() in {"_no response_", "（无）", "(none)"}: return ""
        if "HTML 源码（可选）" in names:
            value = re.sub(r"^" + re.escape(FENCE) + r"[^\n]*\n", "", value)
            value = re.sub(r"\n" + re.escape(FENCE) + r"\s*$", "", value)
        return value
    return {"case_name":field("案例名称"),"author":field("作者署名（可选）","作者署名"),
            "case_type":field("投稿类型"),"data_source":field("数据来源"),
            "summary":field("一句话介绍与设计思路"),
            "notes":field("运行方式、已知限制或补充说明（可选）","运行方式、已知限制或补充说明"),
            "html_source":field("HTML 源码（可选）")}


def write_result(result: dict) -> None:
    (ROOT / "case-submission-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _main() -> int:
    body = os.environ.get("ISSUE_BODY", "")
    try: issue_number = int(os.environ.get("ISSUE_NUMBER", "0") or "0")
    except (TypeError, ValueError): issue_number = 0
    fields = parse_submission_fields(body)
    zip_url = find_zip_url(body) or ""
    result = {"issue_number":issue_number, **fields, "html_source_present":bool(fields["html_source"].strip()),
              "zip_url":zip_url, "red":[], "yellow":[], "conclusion":"review"}
    try:
        with tempfile.TemporaryDirectory(prefix="lifeup-case-check-") as temp:
            tempdir = Path(temp)
            if zip_url:
                archive_path = tempdir / "submission.zip"; download_zip(zip_url, archive_path)
                target = tempdir / "unpacked"; target.mkdir(); safe_extract(archive_path, target)
                if not find_checkable_files(target):
                    write_report("## 自动脱敏检查：需人工复核\n\n未在附件中找到可检查的界面文件。\n\n- 机器结论：**需人工复核**\n- 注意：检查通过不等于正式收录。")
                    result["yellow"] = ["未找到可检查的界面文件"]; return 0
                source_description = "从投稿 Issue 的 ZIP 附件中提取文件"
            else:
                if not fields["html_source"].strip():
                    write_report("## 自动脱敏检查：未能检查\n\n没有检测到 ZIP 附件或 HTML 源码。本次未扫描任何代码；这不代表投稿通过。")
                    result["yellow"] = ["没有 ZIP 附件或 HTML 源码"]; return 0
                target = tempdir / "pasted"; target.mkdir()
                (target / "index.html").write_text(fields["html_source"], encoding="utf-8")
                source_description = "从投稿表单中的 HTML 源码字段读取"
            output, code = run_static_check(target)
            result["red"] = [line.strip() for line in output.splitlines() if re.search(r"^(?:✖ RED|RED )\b", line)]
            result["yellow"] = [line.strip() for line in output.splitlines() if re.search(r"^(?:⚠ YELLOW|YELLOW )\b", line)]
            if code and not result["red"]: result["yellow"].append("静态检查异常退出")
            result["conclusion"] = "reject" if result["red"] else ("review" if result["yellow"] or not fields["case_name"].strip() or not fields["summary"].strip() else "submit")
            status = "发现需处理的 RED 项" if result["conclusion"] == "reject" else ("可提交，仍需人工审核" if result["conclusion"] == "submit" else "需人工复核")
            report = ("## 自动脱敏检查结果\n\n" + f"- 检查来源：{source_description}\n- 机器结论：**{status}**\n"
                      "- 检查方式：静态扫描；没有执行投稿代码。\n- 注意：检查通过不等于正式收录，外部资源、运行效果与授权仍需维护者审核。\n"
                      "> 你上传的截图不会被自动检查，请自行确认画面中没有真实手机 IP、任务内容或其他个人信息。\n\n"
                      "<details>\n<summary>查看检查明细</summary>\n\n~~~text\n" + (output[:12000] or "检查器未返回明细") + "\n~~~\n</details>\n")
            write_report(report); return 0
    except Exception as exc:
        result["conclusion"] = "review"; result["yellow"].append(f"检查异常：{type(exc).__name__}: {exc}")
        try: write_report("## 自动脱敏检查：未完成\n\n" + f"处理投稿时发生错误：{type(exc).__name__}: {exc}\n\n这不代表投稿通过。请维护者人工复核附件。")
        except Exception: pass
        return 0
    finally:
        try: write_result(result)
        except Exception as exc: print(f"无法写入 case-submission-result.json：{type(exc).__name__}: {exc}")



def main() -> int:
    try:
        return _main()
    except Exception as exc:
        try:
            write_result({"issue_number":int(os.environ.get("ISSUE_NUMBER","0") or "0"),"case_name":"","author":"","case_type":"","data_source":"","summary":"","notes":"","html_source":"","html_source_present":False,"zip_url":"","red":[],"yellow":[str(exc)],"conclusion":"review"})
        except Exception: pass
        try: write_report("## 自动脱敏检查：未完成\\n\\n处理投稿时发生未预期错误；需人工复核。")
        except Exception: pass
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
