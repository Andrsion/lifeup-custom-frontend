#!/usr/bin/env python3
"""投稿脱敏与可跑性检查，并可从 HTML 生成社区案例草稿。仅使用 Python 标准库。"""
from __future__ import annotations

import argparse
import html
from html.parser import HTMLParser
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_BYTES = 2 * 1024 * 1024
SCAN_EXTENSIONS = {".html", ".js", ".css", ".json"}
TOKEN_SECRET_RE = re.compile(r'"token"\s*:\s*"[^"]{3,}"')
TOKEN_HEADER_RE = re.compile(r'"tokenHeader"\s*:\s*"([^"]{3,})"')
PHONE_RE = re.compile(r"\b1[3-9]\d{9}\b")
BASE64_RE = re.compile(r"[A-Za-z0-9+/=]{2001,}")
PRIVATE_IP_RE = re.compile(
    r"(?<![\w.])192\.168\.\d{1,3}\.\d{1,3}(?![\w.])"
    r"|(?<![\w.])10(?:\.\d{1,3}){3}(?![\w.])"
    r"|(?<![\w.])172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2}(?![\w.])"
)
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
CSS_COLOR_RE = re.compile(r"--[\w-]+\s*:\s*(#[0-9a-fA-F]{3,8})")
FONT_RE = re.compile(r"font-family\s*:\s*([^;}]+)", re.I)
UI_OBJECT_RE = re.compile(r"\bUI\s*=\s*\{([\s\S]*?)\}")
UI_PAIR_RE = re.compile(r"""([\w$]+)\s*:\s*["']([^"']*)["']""")
EXTERNAL_RE = re.compile(
    r"<script\b[^>]*\bsrc\s*=\s*['\"]https?://|"
    r"<link\b[^>]*\bhref\s*=\s*['\"]https?://|"
    r"@import\s+url\(\s*['\"]?https?://|"
    r"fonts\.googleapis\.com|cdn\.jsdelivr\.net|unpkg\.com|cdnjs\.cloudflare\.com",
    re.I,
)
EXTERNAL_IMAGE_RE = re.compile(r"<img\b[^>]*\bsrc\s*=\s*['\"]https?://", re.I)
INLINE_IMAGE_RE = re.compile(r"data:image/[^;,]+;base64,([A-Za-z0-9+/=]+)", re.I)

# Node.js built-ins; node: prefixed names are also accepted.
NODE_BUILTINS = set("""
assert assert/strict async_hooks buffer child_process cluster console constants crypto
dgram diagnostics_channel dns dns/promises domain events fs fs/promises http http2
https inspector module net os path path/posix path/win32 perf_hooks process punycode
querystring readline readline/promises repl stream stream/consumers stream/promises
stream/web string_decoder sys timers timers/promises tls trace_events tty url util
util/types v8 vm wasi worker_threads zlib test
""".split())


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_depth = 0
        self.h1_depth = 0
        self.nav_depth = 0
        self.open_elements: list[tuple[str, bool]] = []
        self.title_parts: list[str] = []
        self.h1_parts: list[str] = []
        self.nav_parts: list[str] = []
        self.tab_parts: list[str] = []
        self.data_tabs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        lowered = tag.lower()
        self.open_elements.append((lowered, values.get("role") == "tab"))
        if lowered == "title":
            self.title_depth += 1
        if lowered == "h1" and not self.h1_parts:
            self.h1_depth += 1
        if lowered == "nav":
            self.nav_depth += 1
        if values.get("data-tab"):
            self.data_tabs.append(values["data-tab"] or "")

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered == "title" and self.title_depth:
            self.title_depth -= 1
        if lowered == "h1" and self.h1_depth:
            self.h1_depth -= 1
        if lowered == "nav" and self.nav_depth:
            self.nav_depth -= 1
        # Remove the closed element and any malformed nested elements after it.
        for index in range(len(self.open_elements) - 1, -1, -1):
            if self.open_elements[index][0] == lowered:
                del self.open_elements[index:]
                break

    def handle_data(self, data: str) -> None:
        if self.title_depth:
            self.title_parts.append(data)
        if self.h1_depth:
            self.h1_parts.append(data)
        if self.nav_depth:
            self.nav_parts.append(data)
        if any(is_tab for _tag, is_tab in self.open_elements):
            self.tab_parts.append(data)


def unique(values: list[str], limit: int) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        value = " ".join(value.split()).strip()
        if value and value not in seen:
            seen.add(value)
            result.append(value)
            if len(result) >= limit:
                break
    return result


def scan_targets(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if not target.is_dir():
        raise ValueError(f"路径不存在或不是普通文件/目录：{target}")
    files = []
    for path in target.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SCAN_EXTENSIONS:
            continue
        if any(part in {".git", "node_modules"} for part in path.parts):
            continue
        files.append(path)
    return sorted(files, key=lambda p: str(p).casefold())


def line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def relpath(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.name


def read_limited(path: Path) -> tuple[str, bool, int]:
    size = path.stat().st_size
    with path.open("rb") as handle:
        raw = handle.read(MAX_BYTES)
    return raw.decode("utf-8", errors="replace"), size > MAX_BYTES, size


def add_matches(results: list[tuple[str, str, int, str]], level: str, path: Path,
                content: str, pattern: re.Pattern[str], message: str) -> None:
    for match in pattern.finditer(content):
        results.append((level, relpath(path), line_number(content, match.start()), message))


def is_backup_filename(path: Path) -> bool:
    name = path.name.lower()
    if name.endswith(".lfbak"):
        return True
    return "backup" in name and path.suffix.lower() in {
        ".json", ".db", ".sqlite", ".sqlite3", ".csv", ".html", ".js", ".css", ".txt"
    }


def target_has_node_modules(files: list[Path]) -> bool:
    """检查扫描根目录附近是否存在依赖目录（扫描文件列表本身会跳过该目录）。"""
    if not files:
        return False
    try:
        common = Path(__import__("os").path.commonpath([str(p.resolve().parent) for p in files]))
    except (ValueError, OSError):
        return False
    return any((parent / "node_modules").is_dir() for parent in (common, *common.parents))


def check_files(files: list[Path]) -> tuple[list[tuple[str, str, int, str]], dict[str, object]]:
    results: list[tuple[str, str, int, str]] = []
    contents: dict[Path, str] = {}
    total_bytes = 0
    truncated: list[str] = []
    for path in files:
        try:
            content, was_truncated, size = read_limited(path)
        except OSError as exc:
            results.append(("RED", relpath(path), 1, f"无法读取文件：{exc}"))
            continue
        contents[path] = content
        total_bytes += size
        if was_truncated:
            truncated.append(relpath(path))
            results.append(("YELLOW", relpath(path), 1,
                            f"文件超过 2 MB；仅检查前 2 MB（实际 {size} 字节）"))

        if path.name.lower() == "config.json":
            results.append(("RED", relpath(path), 1, "待提交范围包含真实配置文件 config.json"))
        if is_backup_filename(path):
            results.append(("RED", relpath(path), 1, "疑似备份数据文件名（.lfbak / backup）"))

        add_matches(results, "RED", path, content, TOKEN_SECRET_RE, "疑似真实 token")
        for match in TOKEN_HEADER_RE.finditer(content):
            value = match.group(1)
            suspicious_header = (
                re.search(r"bearer\s", value, re.I) is not None
                or len(value) > 60
                or (
                    len(value) >= 20
                    and ("-" in value or "_" in value)
                    and re.search(r"[a-z]", value) is not None
                    and re.search(r"[A-Z]", value) is not None
                )
            )
            results.append((
                "RED" if suspicious_header else "YELLOW",
                relpath(path),
                line_number(content, match.start()),
                "疑似真实密钥被填入 tokenHeader" if suspicious_header
                else "tokenHeader 是请求头名称，请确认没有在这里写密钥",
            ))
        add_matches(results, "RED", path, content, PHONE_RE, "疑似手机号")
        add_matches(results, "RED", path, content, BASE64_RE, "连续 Base64 字符超过 2000")
        if path.name == "config.example.json":
            add_matches(results, "YELLOW", path, content, PRIVATE_IP_RE,
                        "config.example.json 含私网 IP；请确认这是有意保留的示例值")
        else:
            add_matches(results, "RED", path, content, PRIVATE_IP_RE, "出现私网 IP")
        add_matches(results, "YELLOW", path, content, EXTERNAL_RE, "引用外部脚本、样式、字体或 CDN 资源")
        add_matches(results, "YELLOW", path, content, EXTERNAL_IMAGE_RE, "引用外链图片")
        add_matches(results, "YELLOW", path, content, EMAIL_RE, "出现邮箱地址")
        for match in INLINE_IMAGE_RE.finditer(content):
            if len(match.group(1)) > 100 * 1024:
                results.append(("YELLOW", relpath(path), line_number(content, match.start()),
                                "内嵌 Base64 图片超过 100 KB"))

    combined = "\n".join(contents.values())
    green: dict[str, object] = {
        "files": len(files),
        "total_bytes": total_bytes,
        "requests_cloud": bool(re.search(r"/cloud/", combined)),
        "has_upstream_endpoint": bool(re.search(r"/__upstream", combined)),
        "has_node_modules": (
            any("node_modules" in p.parts for p in files)
            or (target_has_node_modules(files))
        ),
        "nonbuiltin_require": [],
        "truncated": truncated,
        "contents": contents,
    }
    require_re = re.compile(r"""\brequire\s*\(\s*["']([^"']+)["']\s*\)""")
    nonbuiltin: list[str] = []
    for path, content in contents.items():
        for match in require_re.finditer(content):
            name = match.group(1)
            if name.startswith((".", "/", "node:")):
                if name.startswith("node:") and name[5:] not in NODE_BUILTINS:
                    nonbuiltin.append(f"{relpath(path)}:{line_number(content, match.start())} require({name!r})")
                continue
            if name not in NODE_BUILTINS:
                nonbuiltin.append(f"{relpath(path)}:{line_number(content, match.start())} require({name!r})")
    green["nonbuiltin_require"] = nonbuiltin
    green["zero_dependency"] = not nonbuiltin and not green["has_node_modules"]
    green["results"] = results
    return results, green


def extract_info(files: list[Path], green: dict[str, object], target: Path) -> dict[str, object]:
    contents: dict[Path, str] = green["contents"]  # type: ignore[assignment]
    combined = "\n".join(contents.values())
    parser = TextExtractor()
    for path in files:
        if path.suffix.lower() == ".html":
            try:
                parser.feed(contents.get(path, ""))
            except Exception:
                pass
    title = "".join(parser.title_parts).strip() or "".join(parser.h1_parts).strip()
    if not title:
        title = target.name if target.is_dir() else target.parent.name
    colors = unique(CSS_COLOR_RE.findall(combined), 8)
    fonts = unique(FONT_RE.findall(combined), 5)
    sections = unique(parser.tab_parts, 30)
    if not sections:
        sections = unique(parser.nav_parts, 30)
    if not sections:
        sections = unique(re.findall(r'data-tab\s*=\s*["\'](.+?)["\']', combined), 30)
    ui_match = UI_OBJECT_RE.search(combined)
    mapping = UI_PAIR_RE.findall(ui_match.group(1)) if ui_match else []
    if not mapping:
        mapping = []

    corpus = (combined + " " + " ".join(fonts)).lower()
    font_text = " ".join(fonts).lower()
    if any(word in corpus for word in ("pixel", "zpix", "fusion", "像素")):
        texture = "像素"
    elif any(word in font_text for word in ("文楷", "快乐体", "手账")):
        texture = "手账"
    elif ("宋体" in font_text or "serif" in font_text) and "sans-serif" not in font_text:
        texture = "报纸"
    elif ("mono" in font_text or "等宽" in font_text) and colors and color_brightness(colors[0]) < 40:
        texture = "终端"
    else:
        texture = "扁平"

    return {
        "title": title,
        "colors": colors,
        "fonts": fonts,
        "sections": sections,
        "mapping": mapping,
        "texture": texture,
    }


def color_brightness(color: str) -> float:
    value = color.lstrip("#")
    if len(value) == 3:
        rgb = [int(ch * 2, 16) for ch in value]
    elif len(value) >= 6:
        rgb = [int(value[i:i + 2], 16) for i in (0, 2, 4)]
    else:
        return 255.0
    return sum(rgb) / 3


def make_draft(info: dict[str, object], green: dict[str, object], slug: str) -> str:
    colors: list[str] = info["colors"]  # type: ignore[assignment]
    fonts: list[str] = info["fonts"]  # type: ignore[assignment]
    sections: list[str] = info["sections"]  # type: ignore[assignment]
    mapping: list[tuple[str, str]] = info["mapping"]  # type: ignore[assignment]
    title = str(info["title"] or "（请手工填写）")
    theme_colors = ", ".join(colors) if colors else "（请手工填写）"
    theme_fonts = ", ".join(fonts) if fonts else "（请手工填写）"
    section_text = "\n".join(f"- {html.escape(item)}" for item in sections) if sections else "（请手工填写）"
    mapped = {key: value for key, value in mapping}
    coin = mapped.get("coin", "（请手工填写）")
    task = mapped.get("tasks", mapped.get("task", "（请手工填写）"))
    data_source = "真实云人升数据" if green["requests_cloud"] else "静态假数据 / 仅设计稿"
    run_type = "可运行示例" if green["requests_cloud"] else "纯设计稿"
    report_lines = [
        f"- 请求 /cloud/：{'是' if green['requests_cloud'] else '否'}",
        f"- 存在 /__upstream：{'是' if green['has_upstream_endpoint'] else '否'}",
        f"- 零依赖（静态检查）：{'是' if green['zero_dependency'] else '否'}",
        f"- 文件数：{green['files']}",
        f"- 总大小：{green['total_bytes']} 字节",
    ]
    return f"""<!-- 由 AI Agent 辅助生成或整理时，请在此保留来源说明；未经维护者审核的草稿不得移入正式案例目录。 -->
# {title}

> 社区投稿 · 类型：{run_type} · 授权：<请作者确认>
> 数据来源：{data_source}

## 一句话
（请作者用一句话说清这套界面想让人产生什么感觉）

## 换名对照
| 人升里的 | 这套叫法 |
| --- | --- |
| 金币 | {coin} |
| 任务 | {task} |

## 界面分区
{section_text}

## 配色与质感
- 质感：{info['texture']}
- 主色：{theme_colors}
- 字体：{theme_fonts}

## 为什么好玩
<!-- 待填：作者视角，别写成功能列表 -->

## 灵感来源
<!-- 待填：从哪个作品/生活场景来 -->

## 机制决定情绪
<!-- 待填：属于「紧迫 / 松弛 / 期待」哪一种，靠哪个机制实现 -->

> 本稿若由 AI 协助整理，请保留文首注释；投稿人需自行确认内容与授权。

## 收录检查
{chr(10).join(report_lines)}
"""


def print_report(results: list[tuple[str, str, int, str]], green: dict[str, object]) -> None:
    order = {"RED": 0, "YELLOW": 1, "GREEN": 2}
    labels = {"RED": "✖", "YELLOW": "⚠", "GREEN": "✓"}
    ordered = sorted(results, key=lambda item: (order[item[0]], item[1], item[2], item[3]))
    if ordered:
        for level, path, line, message in ordered:
            print(f"{labels[level]} {level} {path}:{line} - {message}")
    else:
        print("✓ GREEN 未发现 RED / YELLOW 命中项")
    print("✓ GREEN 摘要")
    print(f"  - 请求 /cloud/：{'是' if green['requests_cloud'] else '否'}")
    print(f"  - 存在 /__upstream：{'是' if green['has_upstream_endpoint'] else '否'}")
    print(f"  - 零依赖（静态检查）：{'是' if green['zero_dependency'] else '否'}")
    for item in green["nonbuiltin_require"]:  # type: ignore[union-attr]
        print(f"  - 非内置 require：{item}")
    print(f"  - 文件数：{green['files']}")
    print(f"  - 总大小：{green['total_bytes']} 字节")
    if green["truncated"]:
        print("  - 截断文件：" + ", ".join(green["truncated"]))  # type: ignore[arg-type]



def main() -> int:
    parser = argparse.ArgumentParser(description="投稿脱敏与可跑性检查 / 案例骨架生成")
    parser.add_argument("path", type=Path, help="HTML 文件或待扫描目录")
    parser.add_argument("--emit", action="store_true", help="检查通过后生成案例骨架")
    parser.add_argument("--slug", help="草稿文件名（与 --emit 同用）")
    parser.add_argument("--force", action="store_true", help="允许覆盖同名草稿")
    parser.add_argument("--no-emit", action="store_true", help="仅检查（兼容显式 CI 调用）")
    parser.add_argument("--quiet", action="store_true", help="仅输出 RED 明细和最终结论")
    args = parser.parse_args()

    if args.emit and not args.slug:
        parser.error("--emit 必须同时提供 --slug")
    if args.slug and not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.slug):
        parser.error("--slug 仅允许小写英文字母、数字和连字符")
    if args.force and not args.emit:
        parser.error("--force 仅能与 --emit 同用")

    try:
        files = scan_targets(args.path.resolve())
        results, green = check_files(files)
        info = extract_info(files, green, args.path.resolve())
    except (OSError, ValueError) as exc:
        print(f"✖ RED {args.path}:1 - {exc}")
        print("结论：不可提交")
        return 2

    if args.quiet:
        for level, path, line, message in results:
            if level == "RED":
                print(f"RED {path}:{line} - {message}")
    else:
        print_report(results, green)
    has_red = any(level == "RED" for level, *_ in results)
    actionable_yellow = any(
        level == "YELLOW" and not (
            (
                path.endswith("config.example.json")
                and message.startswith("config.example.json 含私网 IP")
            )
            or message.startswith("tokenHeader 是请求头名称")
        )
        for level, path, _line, message in results
    )
    conclusion = "不可提交" if has_red else ("需修改后提交" if actionable_yellow else "可提交")
    if args.emit:
        if has_red:
            print("未生成骨架：存在 RED 项，修复后再试。")
            print(f"结论：{conclusion}")
            return 1
        draft_dir = ROOT / "docs" / "cases" / "_drafts"
        draft_path = draft_dir / f"{args.slug}.md"
        if draft_path.exists() and not args.force:
            print(f"未生成骨架：文件已存在 {draft_path.relative_to(ROOT)}；如确认覆盖，请加 --force。")
            print(f"结论：{conclusion}")
            return 1
        draft_dir.mkdir(parents=True, exist_ok=True)
        draft_path.write_text(make_draft(info, green, args.slug), encoding="utf-8")
        print(f"已生成草稿：{draft_path.relative_to(ROOT).as_posix()}")
    print(f"结论：{conclusion}")
    return 1 if has_red else 0


if __name__ == "__main__":
    sys.exit(main())
