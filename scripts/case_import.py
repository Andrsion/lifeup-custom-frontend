#!/usr/bin/env python3
"""Import a reviewed GitHub Issue case; never execute submitted code."""
from __future__ import annotations
import argparse, json, os, re, shutil, subprocess, sys, tempfile, urllib.parse, urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
DRAFTS = ROOT / "docs/cases/_drafts"
REPORT = ROOT / "import-report.md"
SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
FENCE = chr(96) * 3
ATTACHMENT_RE = re.compile(r"https://github\.com/user-attachments/files/[^\s)>]+", re.I)
HTML_BLOCK_RE = re.compile(r"###\s+HTML 源码（可选）\s*\n+\s*" + re.escape(FENCE) + r"html\s*\n(.*?)\n\s*" + re.escape(FENCE), re.I | re.S)
FIELDS = {
    "案例名称": ("案例名称",),
    "作者署名": ("作者署名（可选）", "作者署名"),
    "投稿类型": ("投稿类型",),
    "数据来源": ("数据来源",),
    "一句话介绍与设计思路": ("一句话介绍与设计思路",),
    "HTML 源码（可选）": ("HTML 源码（可选）",),
    "运行方式、已知限制或补充说明": ("运行方式、已知限制或补充说明（可选）", "运行方式、已知限制或补充说明"),
    "投稿确认": ("投稿确认",),
}

def report(text: str, dry_run: bool = False) -> None:
    if not dry_run:
        REPORT.write_text(text.rstrip() + "\n", encoding="utf-8")
    print(text)

def args_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue", type=int, default=int(os.getenv("ISSUE_NUMBER", "0") or "0"))
    parser.add_argument("--slug", default=os.getenv("SLUG", ""))
    parser.add_argument("--dry-run", action="store_true", default=os.getenv("DRY_RUN", "").lower() == "true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--from-result", type=Path)
    parser.add_argument("--stage", action="store_true")
    args = parser.parse_args()
    if args.slug and not SLUG_RE.fullmatch(args.slug): parser.error("--slug 仅允许小写字母、数字和连字符")
    if args.stage and not args.from_result: parser.error("--stage 必须与 --from-result 同用")
    if not args.from_result and args.issue < 1: parser.error("必须提供 ISSUE_NUMBER 或 --issue（正整数）")
    return args

def api_json(url: str, token: str) -> dict:
    req = urllib.request.Request(url, headers={"Accept":"application/vnd.github+json","Authorization":f"Bearer {token}","X-GitHub-Api-Version":"2022-11-28","User-Agent":"lifeup-case-import/1.0"})
    with urllib.request.urlopen(req, timeout=25) as response:
        data=response.read(5*1024*1024+1)
    if len(data)>5*1024*1024: raise ValueError("Issue API 响应超过 5 MB")
    return json.loads(data.decode("utf-8"))

def parse_fields(body: str) -> dict[str,str]:
    sections={}
    headings=list(re.finditer(r"(?m)^###\s+(.+?)\s*$", body))
    for i,m in enumerate(headings):
        end=headings[i+1].start() if i+1<len(headings) else len(body)
        sections[m.group(1).strip()]=body[m.end():end].strip()
    out={}
    for key, labels in FIELDS.items():
        value=next((sections[label] for label in labels if label in sections), "")
        value=re.sub(r"^<!--.*?-->\s*", "", value, flags=re.S).strip()
        if key=="HTML 源码（可选）":
            m=HTML_BLOCK_RE.search("### HTML 源码（可选）\n"+value)
            value=m.group(1).strip() if m else ""
        if value.lower() in {"_no response_","（无）","(none)"}: value=""
        out[key]=value
    return out

def find_zip(body: str) -> str|None:
    matches=[]
    for raw in ATTACHMENT_RE.findall(body):
        url=raw.rstrip(".,;")
        p=urllib.parse.urlparse(url)
        if (p.hostname or "").lower()=="github.com" and p.path.startswith("/user-attachments/files/") and p.path.lower().endswith(".zip"):
            matches.append(url)
    return matches[-1] if matches else None

def helper_functions():
    sys.path.insert(0,str(SCRIPTS))
    from check_case_submission import download_zip, safe_extract
    return download_zip,safe_extract

def check_and_emit(source: Path, slug: str, dry_run: bool):
    checker=SCRIPTS/"case_check.py"
    if dry_run:
        # Keep the isolated checker tree under the outer temporary source directory,
        # which remains alive until the caller has read the generated skeleton.
        root=source.parent/"checker-root"
        (root/"scripts").mkdir(parents=True,exist_ok=True)
        isolated=root/"scripts/case_check.py"; shutil.copy2(checker,isolated)
        (root/"docs/cases/_drafts").mkdir(parents=True,exist_ok=True)
        first=subprocess.run([sys.executable,str(isolated),str(source),"--no-emit"],cwd=root,text=True,capture_output=True,timeout=60)
        output=(first.stdout+"\n"+first.stderr).strip()
        if first.returncode or re.search(r"(?m)^✖ RED\b",output): return output,first.returncode or 1,None
        emitted=subprocess.run([sys.executable,str(isolated),str(source),"--emit","--slug",slug,"--force"],cwd=root,text=True,capture_output=True,timeout=60)
        output+="\n"+(emitted.stdout+"\n"+emitted.stderr).strip()
        return output,emitted.returncode,root/"docs/cases/_drafts"/f"{slug}.md"
    first=subprocess.run([sys.executable,str(checker),str(source),"--no-emit"],cwd=ROOT,text=True,capture_output=True,timeout=60)
    output=(first.stdout+"\n"+first.stderr).strip()
    if first.returncode or re.search(r"(?m)^✖ RED\b",output): return output,first.returncode or 1,None
    emitted=subprocess.run([sys.executable,str(checker),str(source),"--emit","--slug",slug,"--force"],cwd=ROOT,text=True,capture_output=True,timeout=60)
    output+="\n"+(emitted.stdout+"\n"+emitted.stderr).strip()
    return output,emitted.returncode,DRAFTS/f"{slug}.md"

def replace_section(text: str, heading: str, value: str) -> str:
    pattern=re.compile(r"(?ms)^## "+re.escape(heading)+r"\s*\n.*?(?=^## |\Z)")
    replacement=f"## {heading}\n\n{value.strip()}\n\n"
    return pattern.sub(replacement,text,count=1).rstrip()+"\n" if pattern.search(text) else text.rstrip()+"\n\n"+replacement

def build_case(skeleton: str, fields: dict[str,str], author: str) -> str:
    name=fields.get("案例名称","").strip().replace("\n"," ").replace("\r"," ")
    author=(fields.get("作者署名","").strip() or author).replace("\n"," ").replace("\r"," ")
    typ=fields.get("投稿类型","").strip().replace("\n"," ").replace("\r"," ")
    source=fields.get("数据来源","").strip().replace("\n"," ").replace("\r"," ")
    lines=skeleton.splitlines()
    if not lines or not lines[0].startswith("<!--"): raise ValueError("--emit 骨架首行来源注释缺失")
    lines[1:2]=[f"# {name}"]
    for index, line in enumerate(lines):
        if line.startswith("> 社区投稿"):
            lines[index]=f"> 社区投稿 · 作者：{author} · 类型：{typ} · 数据来源：{source} · 授权：<请作者确认>"
        elif line.startswith("> 数据来源："):
            del lines[index]
            break
    text="\n".join(lines).rstrip()+"\n"
    text=replace_section(text,"一句话",fields.get("一句话介绍与设计思路","").strip() or "（投稿人未填写）")
    text=replace_section(text,"补充说明",fields.get("运行方式、已知限制或补充说明","").strip() or "（投稿人未填写运行方式、已知限制或补充说明）")
    for heading,placeholder in [("为什么好玩","<!-- 待填：作者视角，别写成功能列表 -->"),("灵感来源","<!-- 待填：从哪个作品/生活场景来 -->"),("机制决定情绪","<!-- 待填：属于「紧迫 / 松弛 / 期待」哪一种，靠哪个机制实现 -->")]:
        if heading not in text or placeholder not in text: raise ValueError(f"骨架缺少待填章节：{heading}")
    return text

def update_index(text: str, name: str, slug: str, one_liner: str) -> str:
    if "## 已收录" not in text: text=text.rstrip()+"\n\n## 已收录\n"
    entry=f"- [{name}]({slug}.md) —— {one_liner or '（一句话介绍待补）'}"
    start=text.index("## 已收录")+len("## 已收录")
    next_heading=re.search(r"(?m)^##\s+",text[start:])
    end=start+next_heading.start() if next_heading else len(text)
    section=text[start:end]
    if entry not in section: text=text[:start]+section.rstrip()+"\n\n"+entry+"\n"+text[end:]
    return text.rstrip()+"\n"

def update_changelog(text: str, name: str, author: str) -> str:
    heads=list(re.finditer(r"(?m)^## (\d{4}-\d{2}-\d{2})\s*$",text))
    today=date.today().isoformat()
    if not heads or heads[0].group(1)!=today:
        lines=text.splitlines()
        text=(lines[0] if lines else "# 更新日志")+f"\n\n## {today}\n\n"+"\n".join(lines[1:])+"\n"
        heads=list(re.finditer(r"(?m)^## (\d{4}-\d{2}-\d{2})\s*$",text))
    h=heads[0]; nxt=re.search(r"(?m)^##\s+",text[h.end():]); end=h.end()+nxt.start() if nxt else len(text)
    section=text[h.end():end]; entry=f"- 收录社区案例《{name}》（作者：{author}）"
    if entry not in section: text=text[:h.end()]+section.rstrip()+"\n\n"+entry+"\n"+text[end:]
    return text.rstrip()+"\n"

def make_report(fields, issue_no, slug, output, files, status):
    keys=("案例名称","作者署名","投稿类型","数据来源","一句话介绍与设计思路","运行方式、已知限制或补充说明","投稿确认")
    lines=["# 案例导入报告","",f"- Issue：#{issue_no}",f"- slug：{slug}",f"- 结论：**{status}**","","## 已解析字段"]
    for key in keys: lines.append(f"- {key}：{fields.get(key) or '（空，未猜测）'}")
    lines.extend(["","## 静态检查明细","~~~text",output[:12000] or "（无输出）","~~~","","## 文件变更"])
    lines.extend([f"- {p}" for p in files] if files else ["- （没有写入仓库文件）"])
    lines.extend(["","## 仍待人工补充","- 为什么好玩","- 灵感来源","- 机制决定情绪","","没有执行投稿中的任何代码。"])
    return "\n".join(lines)+"\n"

def slugify(value: str, issue_no: int, requested: str = "") -> str:
    if requested: return requested
    clean = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    clean = re.sub(r"-+", "-", clean)
    return clean if clean and re.fullmatch(r"[a-z0-9-]+", clean) else f"issue-{issue_no}"


def plain_external_links(text: str) -> str:
    text = re.sub(r"!\[.*?\]\((https?://[^)\s]+)\)", r"图片/链接：\1", text, flags=re.S)
    return re.sub(r"\[[^\]]*\]\((https?://[^)\s]+)\)", r"图片/链接：\1", text)


def build_staged_markdown(fields: dict[str, str], issue_no: int, skeleton: str, author: str) -> str:
    mapping = {"案例名称":fields.get("case_name",""),"作者署名":fields.get("author","") or author,
               "投稿类型":fields.get("case_type",""),"数据来源":fields.get("data_source",""),
               "一句话介绍与设计思路":fields.get("summary",""),"运行方式、已知限制或补充说明":fields.get("notes","")}
    text = build_case(skeleton, mapping, author)
    lines = text.splitlines()
    if len(lines) < 2: raise ValueError("case_check.py --emit 生成了空骨架")
    lines[0] = f"<!-- 自动导入的未审核草稿 · issue #{issue_no} · 请勿直接发布 -->"
    text = "\n".join(lines) + "\n"
    text = re.sub(r"<!-- 待填[^>]* -->", "<!-- 待填 -->", text)
    text = plain_external_links(text)
    if re.search(r"!\[.*?\]\(https?:", text, re.S) or re.search(r"\[[^\]]*\]\(https?:", text): raise ValueError("外链降级检查失败")
    return text


def main():
    args = args_parse()
    if args.from_result:
        result = json.loads(args.from_result.read_text(encoding="utf-8"))
        issue_no = int(result.get("issue_number") or args.issue or 0)
        if args.stage and result.get("conclusion") != "submit":
            print(f"投稿 #{issue_no} 结论为 {result.get('conclusion')!r}，不生成暂存文件。"); return 0
        fields = {k:str(result.get(k) or "") for k in ("case_name","author","case_type","data_source","summary","notes","zip_url","html_source")}
        html_present = bool(result.get("html_source_present")); author = fields["author"] or "（作者未提供）"
    else:
        repo = os.getenv("GITHUB_REPOSITORY",""); token = os.getenv("GITHUB_TOKEN","")
        if not repo or "/" not in repo: raise ValueError("缺少 GITHUB_REPOSITORY（owner/repo）")
        if not token: raise ValueError("缺少 GITHUB_TOKEN")
        owner, repo_name = repo.split("/",1)
        issue = api_json(f"https://api.github.com/repos/{owner}/{repo_name}/issues/{args.issue}", token)
        body = issue.get("body") or ""; parsed = parse_fields(body)
        fields = {"case_name":parsed.get("案例名称",""),"author":parsed.get("作者署名",""),
                  "case_type":parsed.get("投稿类型",""),"data_source":parsed.get("数据来源",""),
                  "summary":parsed.get("一句话介绍与设计思路",""),"notes":parsed.get("运行方式、已知限制或补充说明",""),
                  "zip_url":find_zip(body) or "","html_source":parsed.get("HTML 源码（可选）","")}
        html_present = bool(fields["html_source"].strip()); issue_no = args.issue
        author = fields["author"] or (issue.get("user") or {}).get("login","") or "（作者未提供）"
    if issue_no < 1: raise ValueError("result.json 缺少有效 issue_number")
    if not args.stage: raise ValueError("正式收录写入路径已移除；请使用 --from-result ... --stage")
    slug = slugify(fields.get("case_name",""), issue_no, args.slug)
    incoming = ROOT / "docs/cases/_incoming"; drafts = ROOT / "docs/cases/_drafts"
    source = drafts / f"{issue_no}-{slug}-src"; target_md = incoming / f"{issue_no}-{slug}.md"
    if target_md.exists(): print(f"暂存文件已存在，保持不覆盖：{target_md.relative_to(ROOT)}"); return 0
    download_zip, safe_extract = helper_functions()
    drafts.mkdir(parents=True, exist_ok=True); source.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="case-stage-") as temp_dir:
        temp = Path(temp_dir); zip_url = fields.get("zip_url","")
        if zip_url:
            archive = temp / "submission.zip"; download_zip(zip_url, archive); safe_extract(archive, source)
        elif html_present and fields.get("html_source"):
            (source / "index.html").write_text(fields["html_source"], encoding="utf-8")
        check_source = source
        if not any(p.is_file() and p.suffix.lower() in {".html",".js",".css",".json"} for p in source.rglob("*")):
            check_source = temp / "skeleton-source"; check_source.mkdir()
            (check_source / "index.html").write_text("<!doctype html><title>未审核草稿</title><h1>待补充</h1>", encoding="utf-8")
        output, code, skeleton_path = check_and_emit(check_source, f"stage-{issue_no}-{slug}", True)
        if code or not skeleton_path or not skeleton_path.is_file(): raise ValueError("case_check.py --emit 未能生成草稿骨架：\n" + output[-3000:])
        markdown = build_staged_markdown(fields, issue_no, skeleton_path.read_text(encoding="utf-8"), author)
        incoming.mkdir(parents=True, exist_ok=True); target_md.write_text(markdown, encoding="utf-8")
        print(f"暂存文件：{target_md.relative_to(ROOT)}")
    try:
        status = subprocess.run(["git","status","--short"], cwd=ROOT, text=True, capture_output=True, check=False)
        print("git status --short：\n" + (status.stdout.rstrip() or "（无输出）"))
    except OSError as exc: print(f"无法读取 git status：{exc}")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"暂存失败：{type(exc).__name__}: {exc}")
        raise
