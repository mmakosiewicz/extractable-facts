#!/usr/bin/env python3
"""Deterministic extractability pass over a live URL or a local draft.

Measures the mechanical half of "can an AI retriever pull a citable, self-contained
fact out of this page": chunk depth, entity density, hedging, orphan references,
heading shape, format opportunities, and (URL mode) visible-vs-structured gaps.

Everything here is countable. Judgement calls — is this actually the answer, is
this claim true, would this rewrite be better — are left to the LLM pass the
skill runs afterwards over the flagged chunks.

Usage:
    extractability.py --url https://example.com/post/
    extractability.py --draft ./article.md
    extractability.py --draft ./article.docx --json out.json

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

# ── tunables ───────────────────────────────────────────────────────────────
CHUNK_WORDS = 150          # retriever-ish passage size
CHUNK_MAX_WORDS = 260      # hard split above this
EARLY_ZONE = 0.30          # Indig: 44.2% of AI citations land in the first 30%
LOW_ENTITY_DENSITY = 2.0   # entities per 100 words below which a chunk reads vague
UA = "Mozilla/5.0 (compatible; ExtractabilityAudit/1.0) extractability-audit"
TIMEOUT = 15.0
FIREWALL_SENTINEL = "blocked by firewall"

HEDGES = [
    "may", "might", "could", "can be", "possibly", "perhaps", "arguably",
    "seems to", "appears to", "tends to", "often", "sometimes", "generally",
    "typically", "usually", "in some cases", "it is believed", "some experts",
    "many believe", "widely considered", "relatively", "fairly", "somewhat",
    "roughly", "more or less", "a number of", "various", "several",
    "potentially", "presumably", "likely", "unlikely", "suggests that",
    "is thought to", "would seem", "to some extent", "up to a point",
]

# Chunk-initial references with no antecedent inside the chunk.
ORPHAN_OPENERS = [
    "this", "that", "these", "those", "it", "they", "them", "he", "she",
    "such", "both", "either", "neither", "here", "there", "the former",
    "the latter", "the above", "the same",
]
GENERIC_REFERENTS = (
    r"data|study|studies|finding|findings|research|result|results|test|tests|"
    r"approach|method|methods|change|changes|issue|problem|point|example|"
    r"number|numbers|figure|figures|chart|table|pattern|trend|effect"
)

BACKREFS = [
    "as mentioned above", "as noted above", "as we saw", "as discussed",
    "as described earlier", "see above", "the previous section",
    "earlier in this", "as explained above", "following on from",
    "in the last section", "as i said", "as we covered",
]

STOPWORD_CAPS = {
    "The", "A", "An", "This", "That", "These", "Those", "It", "They", "We",
    "You", "I", "But", "So", "And", "Or", "If", "When", "While", "For",
    "In", "On", "At", "To", "From", "By", "With", "As", "Then", "Now",
    "Here", "There", "What", "Why", "How", "Which", "Who", "Their", "Its",
    "His", "Her", "Our", "Your", "My", "Not", "No", "Yes", "Most", "Some",
    "Many", "Every", "Each", "All", "One", "Two", "Three", "First", "Second",
    "After", "Before", "Because", "Since", "Although", "However", "Instead",
}

VERBY = re.compile(
    r"\b(is|are|was|were|has|have|do|does|can|should|will|use|find|make|get|"
    r"build|write|fix|check|avoid|choose|run|add|stop|start|improve|why|how|"
    r"what|when|where|which|who)\b", re.I,
)


# ── loading ────────────────────────────────────────────────────────────────
class LoadError(RuntimeError):
    pass


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
            "Allowlist the domain or fetch it through a real browser session."
        )
    if r.status_code >= 400:
        raise LoadError(f"HTTP {r.status_code} from {r.url}")
    return {"html": r.text, "final_url": str(r.url), "status": r.status_code}


def load_draft(path: Path) -> str:
    if not path.exists():
        raise LoadError(f"no such file: {path}")
    suffix = path.suffix.lower()
    if suffix == ".docx":
        try:
            import docx
        except ImportError as exc:
            raise LoadError("python-docx needed for .docx drafts") from exc
        d = docx.Document(str(path))
        out = []
        for p in d.paragraphs:
            text = p.text.strip()
            if not text:
                out.append("")
                continue
            style = (p.style.name or "").lower()
            m = re.search(r"heading (\d)", style)
            out.append(f"{'#' * int(m.group(1))} {text}" if m else text)
        return "\n\n".join(out)
    return path.read_text(encoding="utf-8", errors="replace")


# ── html → markdown-ish ────────────────────────────────────────────────────
_STRIP = re.compile(r"<(script|style|noscript|template|svg)[^>]*>.*?</\1>", re.S | re.I)
_TAG = re.compile(r"<[^>]+>")


def strip_tags(s: str) -> str:
    return " ".join(htmllib.unescape(_TAG.sub(" ", s)).split())


def html_to_text(html: str) -> str:
    """Main-content markdown. trafilatura first; whole-page markdownify as backup.

    Readability extractors sometimes drop every heading on templates with no
    <article>/<main> wrapper, so compare heading counts and keep the richer one.
    """
    body = _STRIP.sub(" ", html)
    best, best_h = "", -1
    try:
        import trafilatura
        md = trafilatura.extract(html, output_format="markdown", include_links=True,
                                 include_tables=True, include_comments=False,
                                 favor_recall=True) or ""
        n = len([l for l in md.splitlines() if l.lstrip().startswith("#")])
        if md:
            best, best_h = md, n
    except Exception:
        pass
    try:
        from bs4 import BeautifulSoup
        from markdownify import markdownify as to_md
        soup = BeautifulSoup(body, "html.parser")
        for t in soup(["nav", "header", "footer", "aside", "form"]):
            t.decompose()
        md = re.sub(r"\n{3,}", "\n\n", to_md(str(soup), heading_style="ATX", strip=["img"])).strip()
        n = len([l for l in md.splitlines() if l.lstrip().startswith("#")])
        if n > best_h or not best:
            best, best_h = md, n
    except Exception:
        pass
    return best or strip_tags(body)


def html_facts(html: str) -> dict:
    """The visible-vs-structured half: what's in JSON-LD but nowhere a human reads."""
    visible = strip_tags(_STRIP.sub(" ", html)).lower()
    blobs, only_structured = [], []
    for m in re.finditer(r"<script[^>]+application/ld\+json[^>]*>(.*?)</script>",
                         html, re.S | re.I):
        raw = m.group(1).strip()
        try:
            data = json.loads(raw)
        except ValueError as exc:
            blobs.append({"ok": False, "error": str(exc)[:120]})
            continue

        def walk(o, path=""):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k.startswith("@"):
                        continue
                    yield from walk(v, f"{path}.{k}" if path else k)
            elif isinstance(o, list):
                for v in o:
                    yield from walk(v, path)
            elif isinstance(o, (str, int, float)) and o not in (True, False):
                yield path, str(o)

        types = re.findall(r'"@type"\s*:\s*"([^"]+)"', raw)
        blobs.append({"ok": True, "types": sorted(set(types))})
        for field, value in walk(data):
            v = value.strip()
            if len(v) < 2 or v.lower().startswith(("http", "data:", "/")):
                continue
            # Drop ISO timestamps, but keep bare figures — a price that lives
            # only in schema is exactly the failure mode worth reporting.
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}[\d\-:+T.Z ]*", v):
                continue
            if re.fullmatch(r"\d{1,3}", v) and re.search(rf"\b{v}\b", visible):
                continue
            if len(v) > 120:
                v = v[:120]
            if v.lower() not in visible:
                only_structured.append({"field": field, "value": v})
    seen, dedup = set(), []
    for row in only_structured:
        k = (row["field"], row["value"])
        if k not in seen:
            seen.add(k)
            dedup.append(row)
    return {
        "jsonld_blobs": blobs,
        "structured_only_facts": dedup[:40],
        "structured_only_count": len(dedup),
        "has_tables": len(re.findall(r"<table\b", html, re.I)),
        "has_article": bool(re.search(r"<article\b", html, re.I)),
        "has_main": bool(re.search(r"<main\b", html, re.I)),
    }


# ── chunking ───────────────────────────────────────────────────────────────
def parse_blocks(md: str) -> list[dict]:
    blocks, heading_stack = [], []
    for raw in re.split(r"\n\s*\n", md):
        block = raw.strip()
        if not block:
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", block)
        if m:
            level, text = len(m.group(1)), m.group(2).strip()
            heading_stack = [h for h in heading_stack if h[0] < level] + [(level, text)]
            blocks.append({"kind": "heading", "level": level, "text": text,
                           "path": [h[1] for h in heading_stack]})
        else:
            kind = "list" if re.match(r"^\s*([-*+]|\d+\.)\s", block) else (
                "table" if block.lstrip().startswith("|") else "para")
            blocks.append({"kind": kind, "text": block,
                           "path": [h[1] for h in heading_stack]})
    return blocks


def chunk(blocks: list[dict]) -> list[dict]:
    """Group blocks into retriever-sized passages that never cross a heading."""
    chunks, buf, buf_words, path, heading = [], [], 0, [], None

    def flush():
        nonlocal buf, buf_words
        if buf:
            chunks.append({"heading": heading, "path": list(path),
                           "text": "\n\n".join(buf)})
            buf, buf_words = [], 0

    for b in blocks:
        if b["kind"] == "heading":
            flush()
            heading, path = b["text"], b["path"]
            continue
        words = len(b["text"].split())
        if buf_words and buf_words + words > CHUNK_MAX_WORDS:
            flush()
        buf.append(b["text"])
        buf_words += words
        if buf_words >= CHUNK_WORDS:
            flush()
    flush()

    total = sum(len(c["text"].split()) for c in chunks) or 1
    running = 0
    for i, c in enumerate(chunks):
        w = len(c["text"].split())
        c["idx"] = i
        c["words"] = w
        c["depth_pct"] = round(100 * running / total, 1)
        running += w
    return chunks


# ── measurements ───────────────────────────────────────────────────────────
def count_entities(text: str) -> dict:
    numbers = re.findall(r"\b\d[\d,.]*\s?%|\b\$\s?\d[\d,.]*|\b\d[\d,.]{1,}\b", text)
    years = re.findall(r"\b(?:19|20)\d{2}\b", text)
    dates = re.findall(
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}\b",
        text, re.I)
    urls = re.findall(r"https?://[^\s)\]]+", text)
    # Proper nouns: capitalised tokens that are not sentence-initial.
    proper = []
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        tokens = re.findall(r"\b[A-Z][A-Za-z0-9&.'’-]+\b", sentence)
        for j, tok in enumerate(tokens):
            if tok in STOPWORD_CAPS:
                continue
            if j == 0 and sentence.strip().startswith(tok):
                continue
            proper.append(tok)
    acronyms = re.findall(r"\b[A-Z]{2,6}\b", text)
    total = len(numbers) + len(years) + len(dates) + len(urls) + len(set(proper)) + len(set(acronyms))
    words = max(len(text.split()), 1)
    return {
        "numbers": len(numbers), "years": len(years), "dates": len(dates),
        "urls": len(urls), "proper_nouns": sorted(set(proper))[:25],
        "acronyms": sorted(set(acronyms))[:12],
        "total": total, "per_100w": round(100 * total / words, 2),
    }


def find_hedges(text: str) -> list[str]:
    low = text.lower()
    return [h for h in HEDGES if re.search(rf"\b{re.escape(h)}\b", low)]


def orphan_signals(text: str) -> list[str]:
    out, low = [], text.lower()
    first = re.split(r"(?<=[.!?])\s+", text.strip())[0] if text.strip() else ""
    fl = first.lower().lstrip("*-# ")
    # Existential "there is/are" and dummy "it is/was" have no antecedent to
    # lose — they read fine standalone, so don't flag them.
    existential = re.match(r"^(?:there|it)\s*(?:['’]s|\s(?:is|are|was|were))\b", fl)
    for opener in ([] if existential else ORPHAN_OPENERS):
        if re.match(rf"^{re.escape(opener)}\b", fl):
            # "This means X" is orphaned; "This report shows" names its subject.
            rest = fl[len(opener):].strip()
            if not re.match(r"^[a-z]+\b", rest) or re.match(
                    r"^(is|are|was|were|means|shows|makes|gives|lets|can|will|would|"
                    r"also|often|usually|matters|helps)\b", rest):
                out.append(f"opens with bare '{opener}'")
            break
    # "this data", "that study" — names a category but not which one. Only a
    # problem when the referent isn't introduced inside the chunk.
    opening = " ".join(fl.split()[:12])
    m = re.search(rf"\b(this|that|these|those)\s+({GENERIC_REFERENTS})\b", opening)
    if m and not re.search(rf"\b(our|the|a|an|we)\s+\w*\s?{m.group(2)}\b",
                           low[len(first):]):
        out.append(f"opens referring to '{m.group(0)}' with no antecedent")
    for phrase in BACKREFS:
        if phrase in low:
            out.append(f"back-reference: '{phrase}'")
    if re.search(r"\b(the (?:first|second|third|next|last) (?:one|step|point|option))\b", low):
        out.append("ordinal reference with no local list")
    return out


def heading_shape(text: str) -> dict:
    words = text.split()
    is_question = text.strip().endswith("?")
    has_verb = bool(VERBY.search(text))
    title_case = (len(words) > 2 and
                  sum(1 for w in words[1:] if w[:1].isupper()) >= max(2, len(words) // 2))
    return {
        "text": text, "words": len(words), "question": is_question,
        "states_something": is_question or has_verb,
        "topic_label_only": not (is_question or has_verb) and len(words) <= 5,
        "too_long": len(words) > 15,
        "title_case": title_case,
    }


def format_opportunities(chunks: list[dict]) -> list[dict]:
    out = []
    for c in chunks:
        t, low = c["text"], c["text"].lower()
        if c.get("kind") == "table":
            continue
        # Comparison prose that wants a table.
        if (len(re.findall(r"\bvs\.?\b|\bcompared (?:to|with)\b|\bwhereas\b|\bwhile\b", low)) >= 2
                and c["words"] > 40):
            out.append({"idx": c["idx"], "type": "table",
                        "why": "repeated comparison language in prose"})
        nums = re.findall(r"\b\d[\d,.]*\s?%|\b\d[\d,.]{2,}\b", t)
        if len(nums) >= 4 and "|" not in t and c["words"] > 40:
            out.append({"idx": c["idx"], "type": "table",
                        "why": f"{len(nums)} figures buried in a paragraph"})
        # A definition that isn't the chunk's opening sentence — a retriever
        # pulling this passage gets the surrounding prose, not the meaning.
        sentences = re.split(r"(?<=[.!?])\s+", t.strip())
        defn = re.compile(
            r"^[A-Z][\w &'’-]{2,40}\s+(?:is|are|refers to|means)\s+(?:a|an|the)\b")
        hit = next((i for i, s in enumerate(sentences) if defn.match(s.strip())), None)
        if hit is not None and hit > 0 and c["words"] > 60:
            out.append({"idx": c["idx"], "type": "definition",
                        "why": f"definition appears in sentence {hit + 1}, not first"})
        # Serial prose that wants a list.
        if len(re.findall(r",\s(?:and\s)?(?:then|next|also|finally)\b", low)) >= 2:
            out.append({"idx": c["idx"], "type": "list",
                        "why": "sequential steps written as prose"})
        if re.search(r"\b(how do|what is|why does|can you|should i)\b", low) and c["words"] > 80:
            out.append({"idx": c["idx"], "type": "faq",
                        "why": "question answered inside a long paragraph"})
    return out


# ── assembly ───────────────────────────────────────────────────────────────
def audit(md: str, *, source: str, mode: str, html: str | None = None) -> dict:
    blocks = parse_blocks(md)
    chunks = chunk(blocks)
    headings = [heading_shape(b["text"]) | {"level": b["level"]}
                for b in blocks if b["kind"] == "heading"]

    for c in chunks:
        c["entities"] = count_entities(c["text"])
        c["hedges"] = find_hedges(c["text"])
        c["orphans"] = orphan_signals(c["text"])
        c["early"] = c["depth_pct"] <= EARLY_ZONE * 100
        flags = []
        if c["entities"]["per_100w"] < LOW_ENTITY_DENSITY and c["words"] >= 40:
            flags.append("low-entity-density")
        if len(c["hedges"]) >= 2:
            flags.append("hedged")
        if c["orphans"]:
            flags.append("not-standalone")
        c["flags"] = flags

    total_words = sum(c["words"] for c in chunks)
    early = [c for c in chunks if c["early"]]
    all_ent = count_entities(md)

    report = {
        "mode": mode,
        "source": source,
        "totals": {
            "words": total_words,
            "chunks": len(chunks),
            "headings": len(headings),
            "entity_density_per_100w": all_ent["per_100w"],
        },
        "early_zone": {
            "cutoff_pct": EARLY_ZONE * 100,
            "chunks": len(early),
            "words": sum(c["words"] for c in early),
            "headings_in_zone": list(dict.fromkeys(
                c["heading"] for c in early if c["heading"])),
            "entity_density_per_100w": count_entities(
                "\n".join(c["text"] for c in early))["per_100w"] if early else 0.0,
        },
        "headings": {
            "topic_label_only": [h["text"] for h in headings if h["topic_label_only"]],
            "too_long": [h["text"] for h in headings if h["too_long"]],
            "title_case": [h["text"] for h in headings if h["title_case"]],
            "questions": sum(1 for h in headings if h["question"]),
            "outline": [{"level": h["level"], "text": h["text"]} for h in headings],
        },
        "flagged": {
            "low_entity_density": [c["idx"] for c in chunks if "low-entity-density" in c["flags"]],
            "hedged": [c["idx"] for c in chunks if "hedged" in c["flags"]],
            "not_standalone": [c["idx"] for c in chunks if "not-standalone" in c["flags"]],
        },
        "format_opportunities": format_opportunities(chunks),
        "chunks": [
            {k: c[k] for k in ("idx", "heading", "depth_pct", "words", "flags",
                               "hedges", "orphans", "text")} |
            {"entity_per_100w": c["entities"]["per_100w"],
             "entity_sample": c["entities"]["proper_nouns"][:8]}
            for c in chunks
        ],
    }
    if html is not None:
        report["visibility"] = html_facts(html)
    return report


# ── rendering ──────────────────────────────────────────────────────────────
def render(rep: dict) -> str:
    L: list[str] = []
    t, ez = rep["totals"], rep["early_zone"]
    L.append(f"EXTRACTABILITY AUDIT — {rep['mode']}: {rep['source']}")
    L.append("=" * 72)
    L.append(f"{t['words']} words · {t['chunks']} retrieval chunks · "
             f"{t['headings']} headings · {t['entity_density_per_100w']} entities/100w")
    L.append("")
    L.append(f"EARLY ZONE (first {ez['cutoff_pct']:.0f}% — where 44.2% of AI citations land)")
    L.append(f"  {ez['chunks']} chunks, {ez['words']} words, "
             f"{ez['entity_density_per_100w']} entities/100w")
    L.append(f"  headings: {', '.join(ez['headings_in_zone']) or '(none)'}")
    L.append("")

    h = rep["headings"]
    L.append("HEADINGS")
    L.append(f"  {h['questions']} phrased as questions")
    for label, key in (("topic label only (names a subject, states nothing)", "topic_label_only"),
                       ("over 15 words", "too_long"),
                       ("Title Case (ignore if that is the site's convention)", "title_case")):
        if h[key]:
            L.append(f"  {len(h[key])} {label}:")
            L.extend(f"      - {x}" for x in h[key][:12])
    L.append("")

    f = rep["flagged"]
    L.append("FLAGGED CHUNKS  (send these to the LLM pass)")
    L.append(f"  not standalone   : {len(f['not_standalone'])}  {f['not_standalone'][:20]}")
    L.append(f"  hedged           : {len(f['hedged'])}  {f['hedged'][:20]}")
    L.append(f"  low entity density: {len(f['low_entity_density'])}  {f['low_entity_density'][:20]}")
    L.append("")

    if rep["format_opportunities"]:
        L.append("FORMAT OPPORTUNITIES")
        for o in rep["format_opportunities"][:20]:
            L.append(f"  chunk {o['idx']:>3}  → {o['type']:<10} {o['why']}")
        L.append("")

    v = rep.get("visibility")
    if v:
        L.append("VISIBLE vs STRUCTURED")
        L.append(f"  JSON-LD blocks: {len(v['jsonld_blobs'])} · "
                 f"<article>: {v['has_article']} · <main>: {v['has_main']} · "
                 f"tables: {v['has_tables']}")
        if v["structured_only_count"]:
            L.append(f"  {v['structured_only_count']} facts exist ONLY in structured data "
                     "(tested AI systems ignore structured data):")
            for row in v["structured_only_facts"][:15]:
                L.append(f"      {row['field']}: {row['value'][:80]}")
        else:
            L.append("  no structured-data-only facts detected")
        L.append("")

    L.append("WORST CHUNKS BY FLAG COUNT")
    worst = sorted(rep["chunks"], key=lambda c: (-len(c["flags"]), c["depth_pct"]))
    for c in [x for x in worst if x["flags"]][:8]:
        L.append(f"  [{c['idx']}] {c['depth_pct']:>5.1f}%  {','.join(c['flags'])}"
                 f"  under: {c['heading'] or '(no heading)'}")
        if c["orphans"]:
            L.append(f"        orphan: {'; '.join(c['orphans'])}")
        if c["hedges"]:
            L.append(f"        hedges: {', '.join(c['hedges'][:8])}")
        L.append(f"        \"{c['text'][:150].replace(chr(10), ' ')}…\"")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", help="live page to audit")
    src.add_argument("--draft", help="local .md / .txt / .docx draft")
    ap.add_argument("--json", help="also write the full report here")
    ap.add_argument("--quiet", action="store_true", help="suppress the text report")
    args = ap.parse_args()

    try:
        if args.url:
            got = load_url(args.url)
            rep = audit(html_to_text(got["html"]), source=got["final_url"],
                        mode="url", html=got["html"])
        else:
            p = Path(args.draft).expanduser()
            rep = audit(load_draft(p), source=str(p), mode="draft")
    except LoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        Path(args.json).write_text(json.dumps(rep, indent=1), encoding="utf-8")
    if not args.quiet:
        print(render(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
