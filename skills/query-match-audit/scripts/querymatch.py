#!/usr/bin/env python3
"""Measure how well a page or draft matches the queries you want it to win,
and how replaceable its content looks.

Two questions, both mechanical here:
  1. MATCH  — do the title, meta description, headings, URL and body actually
     address each target query, or is the answer buried in a broader page?
  2. SUBSTANCE — does the page carry things that are hard to reproduce
     (original data, examples, screenshots, methodology, sourcing), or is it
     a generic summary interchangeable with a dozen others?

Judgement — is this example actually good, is this claim actually supported,
should this be its own page — is left to the reading pass the skill runs after.

Usage:
    querymatch.py --url https://example.com/post/ --queries "ai visibility tools for startups" "best ai visibility tools"
    querymatch.py --draft ./article.md --queries-file ./prompts.txt
    querymatch.py --url https://example.com/ --queries "x" --json out.json

Exit codes: 0 ok, 1 fetch/read failure, 2 bad arguments.
"""
from __future__ import annotations

import argparse
import html as htmllib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

UA = "Mozilla/5.0 (compatible; QueryMatchAudit/1.0) query-match-audit"
TIMEOUT = 15.0
FIREWALL_SENTINEL = "blocked by firewall"

STOP = {
    "a", "an", "and", "are", "as", "at", "be", "best", "but", "by", "can", "do",
    "does", "for", "from", "how", "i", "in", "is", "it", "of", "on", "or", "our",
    "should", "that", "the", "to", "top", "use", "using", "vs", "was", "what",
    "when", "where", "which", "who", "why", "will", "with", "you", "your",
}

# Content types that are expensive to fake and therefore hard to replace.
SUBSTANCE_PATTERNS = {
    "original_data": r"\b(?:we (?:analy[sz]ed|studied|tested|measured|surveyed|tracked|crawled|reviewed)|"
                     r"our (?:study|analysis|data|research|test|survey|experiment|sample)|"
                     r"in our (?:test|study|data|analysis|sample)|"
                     r"we looked at|dataset of|sample of \d)",
    "methodology":   r"\b(?:methodolog|how we (?:did|ran|measured|tested|collected)|"
                     r"we controlled for|margin of error|confidence interval|"
                     r"control group|sample size|we excluded|caveat|limitation)",
    "firsthand":     r"\b(?:we (?:found|built|shipped|ran into|learned)|"
                     r"i (?:tested|tried|built|ran|found|spent)|in my experience|"
                     r"when we|after we|we spent)",
    "examples":      r"\b(?:for example|for instance|e\.g\.|here'?s an example|"
                     r"case study|worked example|walkthrough|step \d)",
    "screenshots":   r"(?:!\[|\[SCREENSHOT:|<img\b|screenshot)",
    "benchmarks":    r"\b(?:benchmark|baseline|versus the|compared (?:against|with) "
                     r"(?:a )?control|before and after|a/b test)",
    "customer":      r"\b(?:customer|our users|support (?:ticket|conversation)|"
                     r"we asked \d|interview(?:ed|s)?|respondents|said in)",
    "expert":        r"\b(?:according to [A-Z]|told us|in an interview|"
                     r"[A-Z][a-z]+ (?:said|argues|notes|points out))",
    "workflow":      r"\b(?:step[- ]by[- ]step|here'?s how to|the process|workflow|"
                     r"prompt:|template:|checklist)",
}

GENERIC_OPENERS = [
    "in today's", "in the world of", "in recent years", "now more than ever",
    "it's no secret", "as technology evolves", "the landscape", "gone are the days",
    "has become increasingly", "plays a crucial role", "plays a vital role",
    "is essential for", "in this digital age", "with the rise of",
]

FILLER_CLAIMS = [
    "studies show", "research shows", "experts agree", "it is widely known",
    "many businesses", "most companies", "industry leaders", "data suggests",
    "statistics show", "it's well known", "surveys indicate",
]


class LoadError(RuntimeError):
    pass


# ── loading ────────────────────────────────────────────────────────────────
def load_url(url: str) -> dict:
    import httpx
    try:
        with httpx.Client(follow_redirects=True, timeout=TIMEOUT,
                          headers={"User-Agent": UA, "Accept": "text/html,*/*"}) as c:
            r = c.get(url)
    except Exception as exc:
        raise LoadError(f"request failed: {type(exc).__name__}: {exc}") from exc
    if r.status_code == 403 and FIREWALL_SENTINEL in r.text[:400]:
        raise LoadError(
            f"blocked by a local outbound firewall/proxy, not by {urlparse(url).netloc}. "
            "Allowlist the domain or fetch it through a real browser session.")
    if r.status_code >= 400:
        raise LoadError(f"HTTP {r.status_code} from {r.url}")
    return {"html": r.text, "final_url": str(r.url)}


def load_draft(path: Path) -> str:
    if not path.exists():
        raise LoadError(f"no such file: {path}")
    if path.suffix.lower() == ".docx":
        try:
            import docx
        except ImportError as exc:
            raise LoadError("python-docx needed for .docx drafts") from exc
        out = []
        for p in docx.Document(str(path)).paragraphs:
            t = p.text.strip()
            if not t:
                out.append("")
                continue
            m = re.search(r"heading (\d)", (p.style.name or "").lower())
            out.append(f"{'#' * int(m.group(1))} {t}" if m else t)
        return "\n\n".join(out)
    return path.read_text(encoding="utf-8", errors="replace")


# ── html ───────────────────────────────────────────────────────────────────
_STRIP = re.compile(r"<(script|style|noscript|template|svg)[^>]*>.*?</\1>", re.S | re.I)
_TAG = re.compile(r"<[^>]+>")


def strip_tags(s: str) -> str:
    return " ".join(htmllib.unescape(_TAG.sub(" ", s)).split())


def page_meta(html: str, url: str) -> dict:
    def meta(pat):
        m = re.search(pat, html, re.I | re.S)
        if not m:
            return None
        c = re.search(r'content\s*=\s*["\']([^"\']*)', m.group(0), re.I)
        return strip_tags(c.group(1)) if c else ""
    title = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    h1 = re.search(r"<h1\b[^>]*>(.*?)</h1>", html, re.S | re.I)
    return {
        "title": strip_tags(title.group(1)) if title else None,
        "description": meta(r'<meta[^>]+name=["\']description["\'][^>]*>'),
        "h1": strip_tags(h1.group(1)) if h1 else None,
        "slug": urlparse(url).path.strip("/").split("/")[-1].replace("-", " ") if url else None,
    }


def html_headings(html: str) -> list[dict]:
    """Headings straight from the HTML.

    Readability extractors drop every heading on templates with no
    <article>/<main> wrapper, so never source headings from the extracted
    markdown in URL mode — the match would silently read 0%.
    """
    out = []
    for m in re.finditer(r"<(h[1-6])\b[^>]*>(.*?)</\1>", _STRIP.sub(" ", html), re.S | re.I):
        t = strip_tags(m.group(2))
        if t:
            out.append({"level": int(m.group(1)[1]), "text": t[:200], "pos": m.start()})
    return out


def html_to_text(html: str) -> str:
    try:
        import trafilatura
        md = trafilatura.extract(html, output_format="markdown", include_links=True,
                                 include_tables=True, favor_recall=True) or ""
        if md:
            return md
    except Exception:
        pass
    try:
        from bs4 import BeautifulSoup
        from markdownify import markdownify as to_md
        soup = BeautifulSoup(_STRIP.sub(" ", html), "html.parser")
        for t in soup(["nav", "header", "footer", "aside", "form"]):
            t.decompose()
        return re.sub(r"\n{3,}", "\n\n", to_md(str(soup), heading_style="ATX")).strip()
    except Exception:
        return strip_tags(_STRIP.sub(" ", html))


def draft_meta(md: str) -> dict:
    fm = re.match(r"^---\n(.*?)\n---\n", md, re.S)
    front = fm.group(1) if fm else ""
    def fld(k):
        m = re.search(rf"^{k}\s*:\s*(.+)$", front, re.M | re.I)
        return m.group(1).strip().strip('"\'') if m else None
    h1 = re.search(r"^#\s+(.+)$", md, re.M)
    return {
        "title": fld("title") or (h1.group(1).strip() if h1 else None),
        "description": fld("description") or fld("meta_description") or fld("meta"),
        "h1": h1.group(1).strip() if h1 else None,
        "slug": fld("slug"),
    }


# ── matching ───────────────────────────────────────────────────────────────
def terms(s: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", (s or "").lower()) if w not in STOP and len(w) > 1]


def coverage(query: str, text: str) -> dict:
    """Which of the query's content words appear, and does the exact phrase?"""
    qt = terms(query)
    low = (text or "").lower()
    present = [w for w in qt if re.search(rf"\b{re.escape(w)}\w*", low)]
    missing = [w for w in qt if w not in present]
    exact = bool(re.search(re.escape(query.lower().strip()), low))
    return {
        "pct": round(100 * len(present) / len(qt), 1) if qt else 0.0,
        "present": present, "missing": missing, "exact_phrase": exact,
    }


def first_mention_depth(query: str, body: str) -> float | None:
    """How far into the body before all the query's terms have appeared."""
    qt = set(terms(query))
    if not qt or not body:
        return None
    words = body.split()
    seen, total = set(), len(words)
    for i, w in enumerate(words):
        wl = re.sub(r"[^a-z0-9]", "", w.lower())
        for t in list(qt - seen):
            if wl.startswith(t):
                seen.add(t)
        if seen == qt:
            return round(100 * i / max(total, 1), 1)
    return None


def match_report(query: str, meta: dict, body: str, headings: list[str]) -> dict:
    head_blob = " \n ".join(headings)
    per = {
        "title": coverage(query, meta.get("title") or ""),
        "description": coverage(query, meta.get("description") or ""),
        "h1": coverage(query, meta.get("h1") or ""),
        "slug": coverage(query, meta.get("slug") or ""),
        "headings": coverage(query, head_blob),
        "body": coverage(query, body),
    }
    # A dedicated page answers the query in its title/H1; a broader page only
    # mentions it somewhere in the body.
    front = max(per["title"]["pct"], per["h1"]["pct"])
    dedicated = front >= 80 or (front >= 60 and per["slug"]["pct"] >= 60)
    section = (not dedicated) and per["headings"]["pct"] >= 80
    depth = first_mention_depth(query, body)
    if dedicated:
        verdict = "dedicated page"
    elif section:
        verdict = "dedicated section"
    elif per["body"]["pct"] >= 80:
        verdict = "buried in body"
    else:
        verdict = "not covered"
    # Which headings look like they address this query.
    qt = set(terms(query))
    matching = [h for h in headings
                if qt and len(qt & set(terms(h))) / len(qt) >= 0.6]
    return {
        "query": query, "verdict": verdict, "per_field": per,
        "first_full_mention_depth_pct": depth,
        "matching_headings": matching[:6],
        "missing_from_title": per["title"]["missing"],
    }


# ── substance ──────────────────────────────────────────────────────────────
def content_images(html: str) -> list[dict]:
    """Article images from raw HTML, excluding theme/template furniture.

    Text extraction drops image markup, so counting screenshots from the
    extracted body reports zero on pages full of them.
    """
    out = []
    for tag in re.findall(r"<img\b[^>]*>", _STRIP.sub(" ", html), re.I):
        src = re.search(r'(?:data-src|src)\s*=\s*["\']([^"\']+)', tag, re.I)
        if not src:
            continue
        u = src.group(1)
        if u.startswith("data:"):
            continue
        is_content = ("/uploads/" in u) or ("/wp-content/" in u and "/themes/" not in u)
        if not is_content:
            continue
        alt = re.search(r'\balt\s*=\s*["\']([^"\']*)["\']', tag, re.I)
        out.append({"file": u.rsplit("/", 1)[-1][:60],
                    "alt": alt.group(1) if alt else None})
    return out


def substance(body: str, images: list[dict] | None = None) -> dict:
    low = body.lower()
    hits = {}
    for name, pat in SUBSTANCE_PATTERNS.items():
        found = re.findall(pat, body, re.I)
        hits[name] = len(found)
    if images is not None:
        hits["screenshots"] = len(images)
    words = max(len(body.split()), 1)
    numbers = len(re.findall(r"\b\d[\d,.]*\s?%|\b\$\s?\d[\d,.]*|\b\d[\d,.]{2,}\b", body))
    links = re.findall(r"\[[^\]]+\]\((https?://[^)]+)\)", body)
    ext = [u for u in links if "://" in u]
    domains = sorted({urlparse(u).netloc.replace("www.", "") for u in ext})
    generic = [g for g in GENERIC_OPENERS if g in low]
    filler = [f for f in FILLER_CLAIMS if f in low]
    # Unsupported filler: "studies show" with no link in the same sentence.
    unsupported = []
    for sent in re.split(r"(?<=[.!?])\s+", body):
        sl = sent.lower()
        if any(f in sl for f in FILLER_CLAIMS) and "](http" not in sent:
            unsupported.append(sent.strip()[:160])
    present = [k for k, v in hits.items() if v]
    return {
        "signals": hits,
        "images": images or [],
        "images_missing_alt": sum(1 for i in (images or []) if not i.get("alt")),
        "signal_types_present": len(present),
        "signal_types_total": len(SUBSTANCE_PATTERNS),
        "present": present,
        "absent": [k for k, v in hits.items() if not v],
        "numbers": numbers,
        "numbers_per_1000w": round(1000 * numbers / words, 1),
        "external_links": len(ext),
        "source_domains": domains[:20],
        "generic_openers": generic,
        "filler_claims": filler,
        "unsupported_claims": unsupported[:10],
        "words": words,
    }


def section_depth(md: str) -> list[dict]:
    """Word count under each H2 — thin sections are the usual coverage gap."""
    out, cur, buf = [], None, []
    for line in md.splitlines():
        m = re.match(r"^(#{2,3})\s+(.*)$", line)
        if m:
            if cur:
                out.append({"heading": cur, "words": len(" ".join(buf).split())})
            cur, buf = m.group(2).strip(), []
        elif cur:
            buf.append(line)
    if cur:
        out.append({"heading": cur, "words": len(" ".join(buf).split())})
    return out


def headings_of(md: str) -> list[str]:
    return [m.group(2).strip() for m in re.finditer(r"^(#{1,6})\s+(.*)$", md, re.M)]


CHROME_HEADINGS = re.compile(
    r"^(keep learning|related|you might also like|recommended|further reading|"
    r"newsletter|subscribe|your weekly|blog|product|company|resources|"
    r"follow us|share this|comments|about the author|categories|tags)\b", re.I)


def mark_chrome(secs: list[dict], *, url_mode: bool) -> None:
    """Tag template furniture so thin-section findings don't report the footer.

    Only meaningful for a fetched page: a draft has no nav, related-posts rail
    or newsletter block, and its sections are legitimately short early on.
    Heuristic, not authoritative — the renderer marks these with a question
    mark rather than dropping them.
    """
    for i, s in enumerate(secs):
        if not url_mode:
            s["chrome"] = False
            continue
        tail = i >= len(secs) - 10
        s["chrome"] = bool(CHROME_HEADINGS.match(s["heading"])) or (tail and s["words"] < 60)


def html_sections(html: str) -> list[dict]:
    """Section word counts measured on the HTML itself.

    Needed because readability extraction can drop heading markup entirely, in
    which case the heading text is nowhere in the extracted body and section
    boundaries can't be recovered from it.
    """
    clean = _STRIP.sub(" ", html)
    hs = [(m.start(), m.end(), int(m.group(1)[1]), strip_tags(m.group(2)))
          for m in re.finditer(r"<(h[1-6])\b[^>]*>(.*?)</\1>", clean, re.S | re.I)]
    hs = [h for h in hs if h[3]]
    out = []
    for n, (_, end, lvl, text) in enumerate(hs):
        stop = hs[n + 1][0] if n + 1 < len(hs) else len(clean)
        out.append({"heading": text, "level": lvl,
                    "words": len(strip_tags(clean[end:stop]).split())})
    return out


# ── assembly ───────────────────────────────────────────────────────────────
def audit(md: str, meta: dict, queries: list[str], *, source: str, mode: str,
          headings: list[str] | None = None,
          sections: list[dict] | None = None,
          images: list[dict] | None = None) -> dict:
    hs = headings if headings is not None else headings_of(md)
    body = re.sub(r"^#{1,6}\s+.*$", "", md, flags=re.M)
    matches = [match_report(q, meta, body, hs) for q in queries]
    secs = sections if sections is not None else section_depth(md)
    mark_chrome(secs, url_mode=(mode == "url"))
    return {
        "mode": mode, "source": source, "meta": meta,
        "queries": matches,
        "substance": substance(body, images),
        "sections": secs,
        "thin_sections": [s for s in secs if 0 < s["words"] < 120 and not s.get("chrome")],
        "headings": hs,
    }


def render(r: dict) -> str:
    L = [f"QUERY-MATCH AUDIT — {r['mode']}: {r['source']}", "=" * 72]
    m = r["meta"]
    L.append(f"title : {m.get('title') or '(none)'}")
    L.append(f"meta  : {m.get('description') or '(none)'}")
    if m.get("h1") and m.get("h1") != m.get("title"):
        L.append(f"h1    : {m['h1']}")
    L.append("")

    L.append("QUERY MATCH")
    for q in r["queries"]:
        L.append(f"  \"{q['query']}\"  →  {q['verdict'].upper()}")
        p = q["per_field"]
        L.append(f"      title {p['title']['pct']:>5.1f}%  h1 {p['h1']['pct']:>5.1f}%  "
                 f"slug {p['slug']['pct']:>5.1f}%  headings {p['headings']['pct']:>5.1f}%  "
                 f"body {p['body']['pct']:>5.1f}%")
        if q["missing_from_title"]:
            L.append(f"      missing from title: {', '.join(q['missing_from_title'])}")
        if q["first_full_mention_depth_pct"] is not None:
            L.append(f"      all query terms first co-occur at {q['first_full_mention_depth_pct']}% depth")
        if q["matching_headings"]:
            L.append(f"      addressed by: {q['matching_headings'][0]}")
        L.append("")

    s = r["substance"]
    L.append(f"SUBSTANCE  ({s['signal_types_present']}/{s['signal_types_total']} hard-to-reproduce signals present)")
    L.append(f"  present : {', '.join(s['present']) or '(none)'}")
    L.append(f"  ABSENT  : {', '.join(s['absent']) or '(none)'}")
    L.append(f"  {s['numbers']} figures ({s['numbers_per_1000w']}/1000w) · "
             f"{s['external_links']} external links · {len(s['source_domains'])} distinct sources")
    if s.get("images"):
        miss = s["images_missing_alt"]
        L.append(f"  {len(s['images'])} content images"
                 + (f" ({miss} missing alt text)" if miss else " (all have alt text)"))
    if s["source_domains"]:
        L.append(f"  sources : {', '.join(s['source_domains'][:8])}")
    if s["generic_openers"]:
        L.append(f"  generic openers: {', '.join(s['generic_openers'])}")
    if s["unsupported_claims"]:
        L.append(f"  unsupported appeals to authority ({len(s['unsupported_claims'])}):")
        for c in s["unsupported_claims"][:5]:
            L.append(f"      \"{c}\"")
    L.append("")

    if r["thin_sections"]:
        L.append("THIN SECTIONS (<120 words)")
        for t in r["thin_sections"][:12]:
            L.append(f"  {t['words']:>4}w  {t['heading']}")
        L.append("")

    L.append("SECTION DEPTH")
    for sec in r["sections"][:30]:
        tag = "  (chrome?)" if sec.get("chrome") else ""
        L.append(f"  {sec['words']:>5}w  {sec['heading'][:70]}{tag}")
    if any(s.get("chrome") for s in r["sections"]):
        L.append("  note: '(chrome?)' rows look like template furniture "
                 "(related posts, newsletter, footer) — confirm before reporting them.")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--url")
    src.add_argument("--draft")
    q = ap.add_mutually_exclusive_group(required=True)
    q.add_argument("--queries", nargs="+", help="target queries / prompts")
    q.add_argument("--queries-file", help="one query per line")
    ap.add_argument("--json")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    queries = a.queries or [l.strip() for l in Path(a.queries_file).read_text().splitlines()
                            if l.strip() and not l.startswith("#")]
    if not queries:
        print("error: no queries given", file=sys.stderr)
        return 2

    try:
        if a.url:
            got = load_url(a.url)
            md = html_to_text(got["html"])
            meta = page_meta(got["html"], got["final_url"])
            hs = [h["text"] for h in html_headings(got["html"])]
            rep = audit(md, meta, queries, source=got["final_url"], mode="url",
                        headings=hs, sections=html_sections(got["html"]),
                        images=content_images(got["html"]))
        else:
            p = Path(a.draft).expanduser()
            md = load_draft(p)
            rep = audit(md, draft_meta(md), queries, source=str(p), mode="draft")
    except LoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if a.json:
        Path(a.json).write_text(json.dumps(rep, indent=1), encoding="utf-8")
    if not a.quiet:
        print(render(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
