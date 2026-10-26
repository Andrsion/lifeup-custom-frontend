#!/usr/bin/env python3
"""轻量仓库质量检查：链接、示例配置、JS 语法与 llms 生成确定性。"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NODE_FILES = [
    ROOT / "examples/minimal-html/proxy.js",
    ROOT / "examples/desktop-dashboard/proxy.js",
    ROOT / "examples/group-bot/bot.js",
    ROOT / "scripts/doctor.js",
    ROOT / "scripts/test_proxy.js",
]
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def check_json() -> list[str]:
    errors: list[str] = []
    for path in sorted((ROOT / "examples").rglob("config.example.json")):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: JSON 无效：{exc}")
    return errors


def check_javascript() -> list[str]:
    if shutil.which("node") is None:
        return [
            "无法运行 JavaScript 语法检查：未找到 Node.js。"
            "请安装 Node.js，并确认 node 已加入 PATH。"
        ]
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
        if not re.search(r"api_result\s*===\s*false", content):
            errors.append(f"{html.relative_to(ROOT)}: 写操作必须显式识别 api_result=false 的业务失败")
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
    markdown_files = [ROOT / "README.md", ROOT / "llms.txt", ROOT / "CONTRIBUTING.md", ROOT / "CHANGELOG.md"]
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
    if "## 文档目录（自动生成）" not in content:
        return ["llms-full.txt 缺少自动生成的文档目录"]
    toc = content.split("<!-- ===== ", 1)[0]
    if "— docs/api-cheatsheet.md" not in toc:
        return ["llms-full.txt 文档目录缺少 API 速查表"]
    if "— docs/ai-build-standard.md" not in toc:
        return ["llms-full.txt 文档目录缺少 AI 施工标准"]
    if "<!-- ===== docs/specs/" in content:
        return ["llms-full.txt 不应收录 docs/specs/ 可选主题文档"]
    llms_index = ROOT / "llms.txt"
    if not llms_index.is_file():
        return ["缺少 llms.txt AI 导航入口"]
    index_text = llms_index.read_text(encoding="utf-8")
    for required in ("按任务路由", "不臆造接口", "写操作不自动重试", "权威来源与分工", "llms-full.txt"):
        if required not in index_text:
            return [f"llms.txt 缺少关键导航规则：{required}"]
    return []



def check_case_examples() -> list[str]:
    """Run the submission checker against each runnable HTML example, offline."""
    checker = ROOT / "scripts" / "case_check.py"
    errors: list[str] = []
    example_dirs = sorted(
        path.parent for path in (ROOT / "examples").rglob("index.html")
        if path.is_file()
    )
    for directory in example_dirs:
        result = subprocess.run(
            [sys.executable, str(checker), str(directory), "--no-emit", "--quiet"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        relative = directory.relative_to(ROOT).as_posix()
        conclusion = next(
            (line for line in result.stdout.splitlines() if line.startswith("结论：")),
            "",
        )
        if result.returncode != 0 or conclusion != "结论：可提交":
            red_lines = [
                line for line in result.stdout.splitlines()
                if line.startswith("RED ")
            ]
            detail = "\\n".join(red_lines) if red_lines else (
                result.stderr.strip() or result.stdout.strip() or "未输出结论"
            )
            errors.append(
                f"{relative}: case_check.py 回归失败（{conclusion or '缺少结论'}）\\n{detail}"
            )
    if not errors:
        print(f"✓ 投稿脱敏回归通过：{len(example_dirs)} 个含 index.html 的示例目录均非 RED。")
    return errors



def check_case_checker_fixtures() -> list[str]:
    """Exercise RED detection, clean HTML, and draft emission using disposable files."""
    checker = ROOT / "scripts" / "case_check.py"
    errors: list[str] = []
    draft_dir = ROOT / "docs" / "cases" / "_drafts"
    draft_dir_existed = draft_dir.exists()
    slug = f"case-check-ci-smoke-{__import__('os').getpid()}"
    draft_path = draft_dir / f"{slug}.md"
    marker = "<!-- 由 AI Agent 辅助生成或整理时，请在此保留来源说明；未经维护者审核的草稿不得移入正式案例目录。 -->"
    try:
        with tempfile.TemporaryDirectory(prefix="case-check-fixture-") as temp_dir:
            temp_root = Path(temp_dir)
            red_html = temp_root / "red.html"
            red_html.write_text(
                '<html><body>{"token":"abcdef123456"} 192.168.1.50</body></html>',
                encoding="utf-8",
            )
            red_result = subprocess.run(
                [sys.executable, str(checker), str(red_html), "--no-emit", "--quiet"],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            red_output = red_result.stdout
            if (
                red_result.returncode == 0
                or "结论：不可提交" not in red_output
                or "疑似真实 token" not in red_output
                or "出现私网 IP" not in red_output
            ):
                errors.append(
                    "case_check.py RED fixture failed: expected token and private-IP REDs; "
                    + (red_output or red_result.stderr)
                )
            else:
                print("✓ case_check.py RED 临时用例通过：token 与私网 IP 均为 RED。")

            token_fixtures = [
                ('{token:"abcdef123456"}', "key-value"),
                ('const token="abcdef123456"', "key-value"),
                ('fetch("/x?token=abcdef123456")', "url-query"),
                ('Authorization: "Bearer abcdef123456"', "authorization-bearer"),
                ('localStorage.setItem("lifeup-token","abcdef123456")', "setItem-token-key"),
                ('{"X-LifeUp-Token":"abcdefghijklmnop"}', "custom-token-header"),
            ]
            for index, (payload, mode) in enumerate(token_fixtures):
                token_file = temp_root / f"token-{index}.html"
                token_file.write_text(payload, encoding="utf-8")
                token_result = subprocess.run(
                    [sys.executable, str(checker), str(token_file), "--no-emit", "--quiet"],
                    cwd=ROOT, text=True, capture_output=True, check=False,
                )
                if token_result.returncode == 0 or mode not in token_result.stdout:
                    errors.append(f"token fixture {mode} failed: " + (token_result.stdout or token_result.stderr))
                else:
                    print(f"✓ token 检测模式 {mode} 临时用例通过。")

            placeholder_file = temp_root / "placeholder.html"
            placeholder_file.write_text('{token:"your-token-here"} {token:"example-secret"}', encoding="utf-8")
            placeholder_result = subprocess.run(
                [sys.executable, str(checker), str(placeholder_file), "--no-emit", "--quiet"],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            if placeholder_result.returncode != 0 or "疑似真实 token" in placeholder_result.stdout:
                errors.append("token placeholder whitelist failed: " + placeholder_result.stdout)
            else:
                print("✓ token 占位符白名单临时用例通过。")

            header_file = temp_root / "token-header.html"
            header_file.write_text('tokenHeader:"Authorization"', encoding="utf-8")
            header_result = subprocess.run(
                [sys.executable, str(checker), str(header_file), "--no-emit", "--quiet"],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            if header_result.returncode != 0 or "结论：可提交" not in header_result.stdout:
                errors.append("tokenHeader false-positive fixture failed: " + header_result.stdout)
            else:
                print("✓ tokenHeader 请求头名称误判回归用例通过。")

            clean_html = temp_root / "clean.html"
            clean_html.write_text("<h1>测试</h1>", encoding="utf-8")
            clean_result = subprocess.run(
                [sys.executable, str(checker), str(clean_html), "--no-emit", "--quiet"],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            if clean_result.returncode != 0 or "结论：可提交" not in clean_result.stdout:
                errors.append(
                    "case_check.py clean fixture failed: "
                    + (clean_result.stdout or clean_result.stderr)
                )
            else:
                print("✓ case_check.py 纯标题临时用例通过：结论为可提交。")

            emit_result = subprocess.run(
                [sys.executable, str(checker), str(clean_html), "--emit", "--slug", slug, "--quiet"],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            if emit_result.returncode != 0 or not draft_path.is_file():
                errors.append(
                    "case_check.py --emit fixture failed: "
                    + (emit_result.stdout or emit_result.stderr)
                )
            elif marker not in draft_path.read_text(encoding="utf-8").splitlines()[0]:
                errors.append(
                    "case_check.py --emit fixture failed: first line missing AI-source comment; "
                    + draft_path.read_text(encoding="utf-8").splitlines()[0]
                )
            else:
                print("✓ case_check.py --emit 临时用例通过：草稿首行含来源注释。")
    finally:
        draft_path.unlink(missing_ok=True)
        if not draft_dir_existed:
            try:
                draft_dir.rmdir()
            except OSError:
                pass
    return errors


def check_case_submission_and_import_fixtures() -> list[str]:
    """Exercise the import parser, dry-run isolation, and attachment fallback reports."""
    errors: list[str] = []
    import importlib.util

    def load_module(name: str, path: Path):
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    importer = load_module("case_import_fixture", ROOT / "scripts" / "case_import.py")
    fence = chr(96) * 3
    body = (
        "### 案例名称\n冒险者面板\n"
        "### 作者署名（可选）\n作者甲\n"
        "### 投稿类型\n静态设计稿 / 假数据演示\n"
        "### 数据来源\n静态假数据\n"
        "### 一句话介绍与设计思路\n用轻量卡片展示任务，强调松弛感。\n"
        "### HTML 源码（可选）\n" + fence + "html\n<h1>示例</h1>\n" + fence + "\n"
        "### 运行方式、已知限制或补充说明（可选）\n直接打开 index.html。\n"
        "### 投稿确认\n- [x] 已确认\n"
    )
    fields = importer.parse_fields(body)
    if fields.get("案例名称") != "冒险者面板" or fields.get("作者署名") != "作者甲":
        errors.append("case_import failed to parse name or author")
    if fields.get("HTML 源码（可选）") != "<h1>示例</h1>":
        errors.append("case_import failed to extract fenced HTML")
    else:
        print("✓ case_import Issue 字段与 HTML 源码解析通过。")

    skeleton = (
        "<!-- AI 来源注释；未经审核 -->\n# 原标题\n\n"
        "> 社区投稿 · 类型：设计稿 · 授权：<请作者确认>\n"
        "> 数据来源：静态假数据\n\n## 一句话\n（待填）\n\n"
        "## 为什么好玩\n<!-- 待填：作者视角，别写成功能列表 -->\n\n"
        "## 灵感来源\n<!-- 待填：从哪个作品/生活场景来 -->\n\n"
        "## 机制决定情绪\n<!-- 待填：属于「紧迫 / 松弛 / 期待」哪一种，靠哪个机制实现 -->\n"
    )
    rendered = importer.build_case(skeleton, fields, "github-user")
    if not rendered.startswith("<!-- AI 来源注释；未经审核 -->\n# 冒险者面板"):
        errors.append("case_import did not preserve source comment or set H1")
    if "作者：作者甲" not in rendered or "直接打开 index.html。" not in rendered:
        errors.append("case_import did not map author/supplement")
    if "## 为什么好玩\n<!-- 待填：" not in rendered:
        errors.append("case_import changed a required human-fill section")
    index = importer.update_index("## 投稿\n说明。\n", "冒险者面板", "adventurer-panel", "轻量卡片")
    if "## 已收录" not in index or "- [冒险者面板](adventurer-panel.md)" not in index:
        errors.append("case_import did not create collection index")
    log = importer.update_changelog("# 更新日志\n\n说明。\n", "冒险者面板", "作者甲")
    if "收录社区案例《冒险者面板》（作者：作者甲）" not in log:
        errors.append("case_import did not update CHANGELOG")
    if not errors:
        print("✓ case_import 骨架、人工待填章节、索引与 CHANGELOG 逻辑通过。")

    submission = load_module("case_submission_fixture", ROOT / "scripts" / "check_case_submission.py")
    with tempfile.TemporaryDirectory(prefix="case-submit-fixture-") as tmp:
        temp = Path(tmp)
        empty = temp / "empty"
        empty.mkdir()
        if submission.find_checkable_files(empty):
            errors.append("empty attachment should have no checkable source files")
        (empty / "screenshot.png").write_bytes(b"fixture")
        if submission.find_checkable_files(empty):
            errors.append("screenshots must not count as source code")
        (empty / "app.js").write_text("const demo = true;", encoding="utf-8")
        if len(submission.find_checkable_files(empty)) != 1:
            errors.append("JS should count as a checkable source file")
        if not errors:
            print("✓ 投稿附件文件类型统计通过（截图不计入源码）。")

        # Exercise the ZIP-with-screenshot-only path without network access.
        report_path = temp / "submission-report.md"
        submission.REPORT = report_path
        archive_path = temp / "screenshots.zip"
        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("screenshot.png", b"fixture")
        submission.find_zip_url = lambda _body: "https://github.com/user-attachments/files/test.zip"
        submission.download_zip = lambda _url, dest: shutil.copyfile(archive_path, dest)
        os_env_before = __import__("os").environ.get("ISSUE_BODY")
        __import__("os").environ["ISSUE_BODY"] = "fixture"
        try:
            submission._main()
        finally:
            if os_env_before is None:
                __import__("os").environ.pop("ISSUE_BODY", None)
            else:
                __import__("os").environ["ISSUE_BODY"] = os_env_before
        report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
        if "未在附件中找到可检查的界面文件" not in report_text or "需人工复核" not in report_text or "可提交" in report_text:
            errors.append("screenshot-only ZIP did not report manual review without saying 可提交")
        elif "截图不会被自动检查" not in report_text:
            errors.append("screenshot-only report omitted screenshot privacy warning")
        else:
            print("✓ 截图-only ZIP 结果为需人工复核，且报告包含截图隐私提示。")

        # Verify unexpected exceptions still create a report.
        submission._main = lambda: (_ for _ in ()).throw(RuntimeError("fixture exception"))
        submission.main()
        report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
        if "自动脱敏检查：未完成" not in report_text or "这不代表投稿通过" not in report_text:
            errors.append("unexpected exception did not create an incomplete report")
        else:
            print("✓ 投稿检查器意外异常兜底报告通过。")

        source = temp / "source"
        source.mkdir()
        (source / "index.html").write_text("<h1>dry run</h1>", encoding="utf-8")
        output, code, draft = importer.check_and_emit(source, "dry-run-fixture", True)
        if code or draft is None or not draft.is_file():
            errors.append("case_import dry-run did not keep generated skeleton available")
        if (ROOT / "docs/cases/_drafts/dry-run-fixture.md").exists():
            errors.append("case_import dry-run wrote a draft into the repository")
        else:
            print("✓ case_import dry-run 只写临时目录且保留骨架通过。")
    return errors



def check_case_import_stage() -> list[str]:
    errors: list[str] = []
    incoming = ROOT / "docs/cases/_incoming"
    incoming_existed = incoming.exists()
    try:
        with tempfile.TemporaryDirectory(prefix="case-import-stage-ci-") as temp_dir:
            temp = Path(temp_dir)
            submit_path = temp / "result-submit.json"
            submit_path.write_text(json.dumps({
                "issue_number":987654321,"case_name":"Test Case","author":"CI","case_type":"静态设计稿",
                "data_source":"静态假数据","summary":"CI 一句话介绍。","notes":"CI 补充说明。",
                "html_source_present":False,"html_source":"","zip_url":"","red":[],"yellow":[],"conclusion":"submit"
            }, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run([sys.executable,str(ROOT/"scripts/case_import.py"),"--from-result",str(submit_path),"--stage","--slug","ci-test"],cwd=ROOT,text=True,capture_output=True,check=False)
            draft = incoming / "987654321-ci-test.md"
            if result.returncode or not draft.is_file():
                errors.append("case_import stage submit failed: " + (result.stdout + "\n" + result.stderr)[-4000:])
            else:
                content = draft.read_text(encoding="utf-8")
                if not content.splitlines() or content.splitlines()[0] != "<!-- 自动导入的未审核草稿 · issue #987654321 · 请勿直接发布 -->": errors.append("stage draft first line does not match required marker")
                if content.count("<!-- 待填 -->") != 3: errors.append(f"expected exactly three generic placeholders; found {content.count('<!-- 待填 -->')}")
                if content.count("](http") != 0: errors.append("stage draft contains external Markdown links")
            reject_path = temp / "result-reject.json"
            reject_path.write_text(json.dumps({"issue_number":987654322,"case_name":"Rejected","author":"CI","case_type":"","data_source":"","summary":"","notes":"","html_source_present":False,"html_source":"","zip_url":"","red":["fixture RED"],"yellow":[],"conclusion":"reject"},ensure_ascii=False),encoding="utf-8")
            before = set(incoming.glob("*.md"))
            rejected = subprocess.run([sys.executable,str(ROOT/"scripts/case_import.py"),"--from-result",str(reject_path),"--stage","--slug","ci-reject"],cwd=ROOT,text=True,capture_output=True,check=False)
            if rejected.returncode or set(incoming.glob("*.md")) != before: errors.append("reject result unexpectedly added a file: " + (rejected.stdout + "\n" + rejected.stderr)[-3000:])
            if not errors: print("✓ 案例暂存回归通过：submit 生成草稿、reject 拒绝生成")
    except Exception as exc: errors.append(f"case_import stage regression raised {type(exc).__name__}: {exc}")
    finally:
        for name in ("987654321-ci-test.md","987654322-ci-reject.md"): (incoming/name).unlink(missing_ok=True)
        if not incoming_existed:
            try: incoming.rmdir()
            except OSError: pass
    return errors


def main() -> int:
    errors = []
    errors += check_json()
    errors += check_javascript()
    errors += check_local_links()
    errors += check_llms_deterministic()
    errors += check_case_examples()
    errors += check_case_checker_fixtures()
    errors += check_case_submission_and_import_fixtures()
    errors += check_case_import_stage()
    if errors:
        print("仓库质量检查失败：")
        for error in errors:
            print(f"\n- {error}")
        return 1
    print("✓ JSON 配置、Node.js/内嵌脚本语法、本地 Markdown 链接、llms-full.txt 确定性检查、案例自动暂存回归均通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
