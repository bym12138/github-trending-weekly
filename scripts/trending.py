"""每周抓取 GitHub Trending，过滤出 AI / 软件 / 产品相关项目，生成周报。

用法：
    python scripts/trending.py            # 生成本周报告
    python scripts/trending.py --no-llm   # 强制只用规则过滤

环境变量：
    GITHUB_TOKEN       可选，用于调用 GitHub API 补充 topics / 创建时间（无 token 限速 60 次/小时）
    ANTHROPIC_API_KEY  可选，有则用 Claude 做相关性判断 + 中文简介 + 本周趋势总结；没有则退回规则过滤
"""

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import rules  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (github-trending-weekly)"
LLM_MODEL = "claude-opus-5-5"


# ---------- 抓取 ----------

def http_get(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def _num(s):
    return int(s.replace(",", "")) if s else 0


def _text(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def parse_trending(page):
    repos = []
    for block in page.split('<article class="Box-row">')[1:]:
        m = re.search(r'<h2 class="h3 lh-condensed">\s*<a[^>]*href="/([^"/]+/[^"/]+)"', block)
        if not m:
            continue
        full_name = m.group(1)
        desc = re.search(r'<p class="col-9[^"]*">(.*?)</p>', block, re.S)
        lang = re.search(r'itemprop="programmingLanguage">(.*?)<', block)
        stars = re.search(r'href="/%s/stargazers"[^>]*>.*?</svg>\s*([\d,]+)' % re.escape(full_name), block, re.S)
        forks = re.search(r'href="/%s/forks"[^>]*>.*?</svg>\s*([\d,]+)' % re.escape(full_name), block, re.S)
        weekly = re.search(r"([\d,]+) stars this week", block)
        repos.append({
            "full_name": full_name,
            "url": f"https://github.com/{full_name}",
            "description": _text(desc.group(1)) if desc else "",
            "language": lang.group(1).strip() if lang else "",
            "stars": _num(stars.group(1) if stars else ""),
            "forks": _num(forks.group(1) if forks else ""),
            "stars_this_week": _num(weekly.group(1) if weekly else ""),
        })
    return repos


def fetch_candidates():
    seen = {}
    for lang in rules.LANGUAGES:
        url = f"https://github.com/trending/{lang}?since=weekly" if lang else "https://github.com/trending?since=weekly"
        try:
            items = parse_trending(http_get(url))
        except Exception as e:  # 单个语言榜失败不影响整体
            print(f"[warn] {url}: {e}", file=sys.stderr)
            continue
        for r in items:
            if r["full_name"] not in seen:
                r["source"] = lang or "all"
                seen[r["full_name"]] = r
        print(f"[fetch] {lang or 'all'}: {len(items)}", file=sys.stderr)
    return list(seen.values())


def enrich(repo, token):
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        data = json.loads(http_get(f"https://api.github.com/repos/{repo['full_name']}", headers))
    except Exception as e:
        print(f"[warn] enrich {repo['full_name']}: {e}", file=sys.stderr)
        repo.setdefault("topics", [])
        return repo
    repo["topics"] = data.get("topics") or []
    repo["created_at"] = (data.get("created_at") or "")[:10]
    repo["homepage"] = data.get("homepage") or ""
    repo["license"] = ((data.get("license") or {}).get("spdx_id")) or ""
    repo["archived"] = data.get("archived", False)
    return repo


# ---------- 规则过滤 ----------

def _hit(text, kw):
    if re.fullmatch(r"[a-z0-9\-\+ ]+", kw):
        return re.search(r"(?<![a-z0-9])" + re.escape(kw) + r"(?![a-z0-9])", text) is not None
    return kw in text  # 中文等直接子串匹配


def rule_classify(repo):
    base = " ".join([repo["full_name"].replace("/", " "), repo["description"]]).lower()
    text = base + " " + " ".join(repo.get("topics", [])).lower()
    # 排除词只看名字和描述，topics 太杂容易误杀
    for kw in rules.EXCLUDE_KEYWORDS:
        if _hit(base, kw.lower()):
            return "other", f"exclude:{kw}"
    for cat, conf in rules.CATEGORIES.items():
        for kw in conf["keywords"]:
            if _hit(text, kw.lower()):
                return cat, f"keyword:{kw}"
    owner = repo["full_name"].split("/")[0]
    if owner in rules.ALLOW_OWNERS:
        return "devtool", f"owner:{owner}"
    return "other", "no-match"


# ---------- Claude 过滤 + 总结（可选） ----------

LLM_SCHEMA = {
    "type": "object",
    "properties": {
        "overview": {
            "type": "array",
            "items": {"type": "string"},
            "description": "本周趋势观察，3-5 条中文要点",
        },
        "repos": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "full_name": {"type": "string"},
                    "category": {"type": "string", "enum": list(rules.CATEGORIES) + ["other"]},
                    "summary_zh": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["full_name", "category", "summary_zh", "reason"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["overview", "repos"],
    "additionalProperties": False,
}

LLM_PROMPT = """你是一名关注 AI、软件开发和产品的技术分析师。下面是本周 GitHub Trending（weekly）的候选仓库，JSON 格式。

任务：
1. 对每个仓库给出 category：
{categories}
   - other: 与 AI / 软件开发 / 产品无关或价值低的噪音（翻墙代理、加密货币、外挂破解、纯学习资料合集、刷星项目等）
2. summary_zh：一句中文简介（不超过 40 字），说清它是什么、解决什么问题，不要照抄英文描述。
3. reason：一句话说明归类理由。
4. overview：结合本周相关项目，写 3-5 条中文趋势观察（例如哪类方向在集中爆发、有哪些值得关注的新项目）。

每个输入仓库都必须出现在 repos 中，full_name 原样保留。rule_hint 是关键词规则的初判，仅供参考。

候选仓库：
{repos}
"""


def llm_classify(repos):
    import anthropic

    cats = "\n".join(f"   - {k}: {v['label']}" for k, v in rules.CATEGORIES.items())
    slim = [
        {
            "full_name": r["full_name"],
            "description": r["description"],
            "language": r["language"],
            "topics": r.get("topics", []),
            "stars_this_week": r["stars_this_week"],
            "rule_hint": r["rule_category"],
        }
        for r in repos
    ]
    client = anthropic.Anthropic()
    response = client.beta.messages.create(
        model=LLM_MODEL,
        max_tokens=32000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={"effort": "medium", "format": {"type": "json_schema", "schema": LLM_SCHEMA}},
        messages=[{
            "role": "user",
            "content": LLM_PROMPT.format(categories=cats, repos=json.dumps(slim, ensure_ascii=False, indent=1)),
        }],
    )
    if response.stop_reason in ("refusal", "max_tokens"):
        raise RuntimeError(f"LLM stop_reason={response.stop_reason}")
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


# ---------- 输出 ----------

def week_id(today):
    y, w, _ = today.isocalendar()
    return f"{y}-W{w:02d}"


def is_new(repo, today, days=30):
    try:
        return (today - dt.date.fromisoformat(repo.get("created_at", ""))).days <= days
    except ValueError:
        return False


def fmt_k(n):
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


def render_report(wid, today, repos, overview, mode, full=True):
    relevant = [r for r in repos if r["category"] != "other"]
    noise = [r for r in repos if r["category"] == "other"]
    lines = [
        f"# GitHub 热点周报 {wid}",
        "",
        f"> 生成于 {today.isoformat()} · 数据源 GitHub Trending (weekly) · 候选 {len(repos)} 个，"
        f"相关 {len(relevant)} 个，过滤 {len(noise)} 个 · 过滤方式：{mode}",
        "",
    ]
    if overview:
        lines += ["## 本周观察", ""] + [f"- {o}" for o in overview] + [""]

    top = sorted(relevant, key=lambda r: -r["stars_this_week"])[:10]
    lines += ["## 🔥 本周 Top 10", "", "| # | 项目 | 简介 | 本周 ⭐ | 总 ⭐ |", "|---|---|---|---|---|"]
    for i, r in enumerate(top, 1):
        new = " 🆕" if is_new(r, today) else ""
        lines.append(f"| {i} | [{r['full_name']}]({r['url']}){new} | {_cell(r)} | +{fmt_k(r['stars_this_week'])} | {fmt_k(r['stars'])} |")
    lines.append("")
    if not full:
        return "\n".join(lines)

    for cat, conf in rules.CATEGORIES.items():
        items = sorted([r for r in relevant if r["category"] == cat], key=lambda r: -r["stars_this_week"])
        if not items:
            continue
        lines += [f"## {conf['label']}（{len(items)}）", "", "| 项目 | 简介 | 语言 | 本周 ⭐ | 总 ⭐ |", "|---|---|---|---|---|"]
        for r in items:
            new = " 🆕" if is_new(r, today) else ""
            lines.append(f"| [{r['full_name']}]({r['url']}){new} | {_cell(r)} | {r['language'] or '-'} | +{fmt_k(r['stars_this_week'])} | {fmt_k(r['stars'])} |")
        lines.append("")

    lines += ["<details>", f"<summary>已过滤的项目（{len(noise)}）</summary>", "", "| 项目 | 描述 | 原因 |", "|---|---|---|"]
    for r in sorted(noise, key=lambda r: -r["stars_this_week"]):
        lines.append(f"| [{r['full_name']}]({r['url']}) | {_esc(r['description'][:80])} | {_esc(r['reason'])} |")
    lines += ["", "</details>", "", "🆕 = 创建不超过 30 天的新仓库", ""]
    return "\n".join(lines)


def _esc(s):
    return s.replace("|", "\\|").replace("\n", " ")


def _cell(r):
    return _esc(r.get("summary_zh") or r["description"] or "-")


README_START = "<!-- WEEKLY:START -->"
README_END = "<!-- WEEKLY:END -->"


def render_readme(readme, wid, summary):
    """只替换 README 中两个标记之间的内容，手写部分保持不动。"""
    archive = sorted(ROOT.glob("reports/*/*.md"), reverse=True)
    report_link = f"reports/{wid[:4]}/{wid}.md"
    body = [
        README_START,
        f"## 📅 最新一期：{wid}",
        "",
        summary.split("\n", 2)[2].strip().replace("## ", "### "),  # 去掉一级标题，二级降为三级
        "",
        f"👉 [查看 {wid} 完整周报（全部分类 + 已过滤项目）]({report_link})",
        "",
        "## 🗂️ 历史周报",
        "",
    ]
    body += [f"- [{p.stem}]({p.relative_to(ROOT).as_posix()})" for p in archive]
    body.append(README_END)
    head, _, rest = readme.partition(README_START)
    _, _, tail = rest.partition(README_END)
    return head + "\n".join(body) + tail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-llm", action="store_true")
    args = ap.parse_args()

    today = dt.date.today()
    wid = week_id(today)
    token = os.environ.get("GITHUB_TOKEN", "")

    repos = fetch_candidates()
    if not repos:
        sys.exit("没有抓到任何仓库，可能 Trending 页面结构变了")
    with ThreadPoolExecutor(8) as pool:
        repos = list(pool.map(lambda r: enrich(r, token), repos))
    repos = [r for r in repos if not r.get("archived")]

    for r in repos:
        r["rule_category"], r["rule_reason"] = rule_classify(r)
        r["category"], r["reason"] = r["rule_category"], r["rule_reason"]

    overview, mode = [], "关键词规则"
    if not args.no_llm and os.environ.get("ANTHROPIC_API_KEY"):
        try:
            result = llm_classify(repos)
            by_name = {x["full_name"]: x for x in result["repos"]}
            for r in repos:
                x = by_name.get(r["full_name"])
                if x:
                    r["category"], r["summary_zh"], r["reason"] = x["category"], x["summary_zh"], x["reason"]
            overview, mode = result["overview"], f"Claude ({LLM_MODEL})"
        except Exception as e:
            print(f"[warn] LLM 失败，退回规则过滤: {e}", file=sys.stderr)

    year = wid[:4]
    data_path = ROOT / "data" / year / f"{wid}.json"
    report_path = ROOT / "reports" / year / f"{wid}.md"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    data_path.write_text(json.dumps(
        {"week": wid, "generated_at": today.isoformat(), "mode": mode, "overview": overview, "repos": repos},
        ensure_ascii=False, indent=2,
    ) + "\n", encoding="utf-8")
    report = render_report(wid, today, repos, overview, mode)
    report_path.write_text(report, encoding="utf-8")
    readme_path = ROOT / "README.md"
    summary = render_report(wid, today, repos, overview, mode, full=False)
    readme_path.write_text(render_readme(readme_path.read_text(encoding="utf-8"), wid, summary), encoding="utf-8")

    n = sum(r["category"] != "other" for r in repos)
    print(f"[done] {wid}: {len(repos)} 候选 -> {n} 相关 ({mode})", file=sys.stderr)


if __name__ == "__main__":
    main()
