# Make facts and data easy to extract for AI

AI search engines don't read a page top to bottom. They split it into chunks, retrieve the passages most relevant to a query, and cite only the fragments that support an answer.

So a page can be well written, accurate, and thoroughly researched, and still never get cited — because its best facts are buried late, hedged into mush, or written so they collapse when lifted out of context.

This repo holds three agent skills for fixing that.

None of this means writing robotic "LLM-friendly" copy. It's mostly good editorial hygiene: make the answer easy to find, keep claims precise, put important information in visible text, and make sure key passages still make sense when read on their own.

| Skill | What it does |
|---|---|
| [`query-match-audit`](skills/query-match-audit) | Checks whether a page matches the queries you want it to win, and whether it offers anything worth retrieving instead of a generic summary. |
| [`ai-extractability-audit`](skills/ai-extractability-audit) | Audits whether AI search engines can chunk, understand, and cite the facts on a page. Returns a concrete rewrite for every finding. |
| [`blog-style-editing`](skills/blog-style-editing) | Edits blog and article prose to a high editorial standard — voice, structure, headings, AI-tell removal. Adapts to whatever house style you give it. |

They stack in that order: be *relevant* enough to retrieve, be *extractable* enough to quote, be *well written* enough to deserve it. All three take a live URL or an unpublished draft.

All three are brand-neutral. None of them asks you to mention any product.

They're in the [Agent Skills](https://code.claude.com/docs/en/skills) format (`SKILL.md` + optional `scripts/` and `references/`), so they work in any agent environment that reads skill folders — Claude Code, Letaido, Codex, ChatGPT Agents. You can also run the audit script directly and ignore the agent part.

---

## query-match-audit

Two questions, in order, against the queries you actually want to win:

1. **Does the page obviously match the query?** Clear from the title, meta description, headings, URL and body — not buried three-quarters of the way down a broader page.
2. **Is there anything here worth retrieving?** Generic summaries are easy to replace. If dozens of pages say essentially the same thing, an AI system has no reason to use yours.

```bash
python3 skills/query-match-audit/scripts/querymatch.py \
  --url https://example.com/post/ \
  --queries "ai visibility tools for startups" "best ai visibility tools"

python3 skills/query-match-audit/scripts/querymatch.py \
  --draft ./article.md --queries-file ./prompts.txt
```

Per query it returns a verdict — **dedicated page** / **dedicated section** / **buried in body** / **not covered** — with per-field coverage across title, H1, slug, headings and body, the terms missing from the title, and how deep into the page the query's terms first co-occur.

For substance it checks nine hard-to-reproduce signals (original data, methodology, firsthand experience, examples, screenshots, benchmarks, customer insight, expert input, workflows), plus figures per 1,000 words, external sourcing, thin sections, generic openers, and unsupported appeals to authority — "studies show" with no link.

```
QUERY MATCH
  "does schema markup help ai citations"  →  DEDICATED PAGE
      title  60.0%  h1  60.0%  slug  60.0%  headings  60.0%  body 100.0%
      missing from title: markup, help

  "ai visibility tools for startups"  →  NOT COVERED
      title  25.0%  h1  25.0%  slug  25.0%  headings  50.0%  body  50.0%

SUBSTANCE  (6/9 hard-to-reproduce signals present)
  present : original_data, methodology, firsthand, examples, benchmarks, expert
  ABSENT  : screenshots, customer, workflow
  28 figures (12.2/1000w) · 9 external links · 2 distinct sources
```

The skill then handles the judgement the script can't: whether a buried query deserves its own page (with the proposed title, H1, slug, and what moves across), and the **replaceability test** — if a competitor could write this page from the same three sources in an afternoon, that's the finding, and it outranks every heading tweak in the report.

**What it can't do is invent real expertise, original data, customer insight, or product facts.** It names exactly what kind of material would fix a generic section; supplying that material is the team's job. Give it access to product docs, customer research, or support conversations and it gets specific — "your support queue has eleven questions about this; three belong in this section".

---

## ai-extractability-audit

Finds the passages AI can't use, and proposes the specific fix for each one.

### Run the script directly

```bash
pip install httpx trafilatura beautifulsoup4 markdownify python-docx

# a live page
python3 skills/ai-extractability-audit/scripts/extractability.py --url https://example.com/post/

# an unpublished draft (.md, .txt, or .docx)
python3 skills/ai-extractability-audit/scripts/extractability.py --draft ./article.md

# machine-readable output for a downstream pass
python3 skills/ai-extractability-audit/scripts/extractability.py --url https://example.com/ --json out.json --quiet
```

Only `httpx` is strictly required. Without `trafilatura`/`beautifulsoup4`/`markdownify` the URL extraction degrades to a plain tag strip; without `python-docx` you lose `.docx` support.

### What it measures

The script splits the content into retriever-sized chunks (≤150 words soft, 260 hard, never crossing a heading) and reports:

- **Answer position** — depth of each chunk, and what sits in the first 30% of the page
- **Entity density** — named things per 100 words, per chunk: people, organizations, products, places, dates, figures, sources
- **Hedging** — a 50-term scan flagging chunks with multiple hedges
- **Standalone failures** — orphan pronouns, back-references ("as mentioned above"), and generic referents ("this chart") with no local antecedent
- **Heading shape** — which headings name a topic without stating anything, which run long, which use Title Case
- **Format opportunities** — where a table, definition, list, or FAQ would beat the paragraph
- **Visible vs structured** (URL mode) — facts present in JSON-LD but absent from visible text

### Example output

```
EXTRACTABILITY AUDIT — url: https://example.com/blog/study/
========================================================================
2364 words · 18 retrieval chunks · 9 headings · 11.14 entities/100w

EARLY ZONE (first 30% — where 44.2% of AI citations land)
  6 chunks, 741 words, 14.84 entities/100w

HEADINGS
  3 topic label only (names a subject, states nothing):
      - Final thoughts
      - Keep learning

FLAGGED CHUNKS  (send these to the LLM pass)
  not standalone   : 1  [14]
  hedged           : 6  [7, 8, 11, 12, 13, 14]
  low entity density: 0  []

FORMAT OPPORTUNITIES
  chunk   2  → table      10 figures buried in a paragraph
  chunk   9  → definition definition appears in sentence 5, not first
```

### What an AI bot actually sees (URL mode)

The audit answers "what can a crawler see on this page?" directly, and reports it even when nothing is wrong:

- **Facts that exist only in structured data.** Tested AI systems ignored JSON-LD, hidden Microdata, and hidden RDFa and relied on visible HTML — so a price that lives only in schema is a price AI search doesn't have. The fix is to surface it in visible copy and keep the schema.
- **Content that survives extraction.** A missing `<article>`/`<main>` wrapper often means a readability pass keeps the prose but drops every heading, erasing the page's structure before chunking. The report gives counts, not adjectives: "4,103 of 4,578 words but 0 of 31 headings".
- **Content that needs JavaScript.** The script fetches raw HTML with no JS execution, the way most crawlers do. If the main content isn't in there, it may not exist for a crawler at all.
- **Addressability.** Headings without `id` attributes can't be deep-linked, so an assistant citing one section has to point at the whole page.

Whether crawlers can *reach* the page — robots.txt, noindex, bot blocking, per-crawler rules — is a separate audit. This one covers what a bot can use once it has the page.

### The script is only half of it

`extractability.py` counts and pattern-matches. **It over-flags on purpose** — it's cheap to run and catches candidates. The `SKILL.md` then directs the judgement pass an agent (or you) performs over the flagged chunks:

- Which hedges are *unnecessary* (evidence supports a firm claim) versus *honest uncertainty* (leave them — stripping a legitimate hedge manufactures a false claim)
- Which passages would actively **mislead** if quoted alone. A caveat paragraph retrieved on its own can read as the main finding. This is the highest-severity finding in the audit.
- Which specific entities are missing — "which five systems? which year?" beats "add more specifics"
- Which format suggestions are genuine

Treating the script's raw output as the finding is the main way this audit goes wrong.

### The hard boundary — and the handoff

**The skill never decides whether a claim is true.** Every rewrite must trace to a source the user supplies or the page already cites. Turning a hedge into a definitive statement without evidence doesn't improve the page — it manufactures a false claim that AI systems may then repeat.

That's a handoff, not a dead end. The audit closes with a short **"Needs a source"** table: the claim as written, the exact question, and the shape of the answer needed ("a % and a sample size"). Supply any of them and the second pass rebuilds the sentence *around* the fact rather than bolting it on — "23% of the 140 teams we measured improved", not "most teams see an improvement (we measured 23%)" — then drops the hedge that was standing in for the missing evidence and re-checks that the chunk still reads standalone.

It uses exactly what you give it: no rounding 23.4% to "nearly a quarter", no upgrading "in our sample" to "across the industry". If your fact turns out to be narrower than the original claim, the rewrite gets narrower too, and says so.

### Research behind the thresholds

- **44.2% of AI citations come from the first 30% of a page** — Kevin Indig's citation research
- **Cited passages favour definitive language over hedging, and carry substantially more named entities than typical prose**
- **Five major AI systems ignored JSON-LD, hidden Microdata, and hidden RDFa, relying on visible HTML** — [Ahrefs test, 2026](https://ahrefs.com/blog/schema-ai-citations/)

These are empirical and will date. Re-check them before leaning on the numbers.

---

## blog-style-editing

Editorial craft rules for blog and article prose: voice, sentence and paragraph discipline, heading conventions, intro and conclusion structure, definition/explanation/answer patterns, link formatting, and a table of AI-tell patterns to cut ("it's not X, it's Y", "this isn't theoretical", dual-audience hedges).

It adapts rather than imposes. A conventions table names what genuinely varies between publications — heading case, person, spelling, contractions, Oxford comma, product-mention policy — with instructions never to silently apply one brand's conventions to another. Where a publication's own guide disagrees, the publication wins.

`references/ahrefs-profile.md` is included as a worked example of a brand profile. Copy its shape for your own publication.

### On product mentions

There is no mention quota. Zero product mentions in an article is a perfectly good outcome, competitors get named plainly where they're the right answer, and the only test is whether the reader needs the tool to do the thing the section is about.

---

## All three return fixes, not observations

Every finding arrives with the replacement text, quoted as current versus proposed. "This paragraph is too long" is an observation; "split after '…ranking factor.'" is a fix. "Your title is weak" is an observation; the proposed title, written out, is a fix. Phrasings like "consider adding specifics" or "could be tightened" are explicitly banned in all three skills.

The exception in each case is material only you can supply — a statistic, a customer example, an original screenshot. Those come back as a specific request ("how many teams, measured how, over what period?"), never as an invented fact.

Rewrites are minimal by design — change the words causing the failure and nothing else. A six-word fix the author accepts beats a rewritten paragraph they argue with.

## Install as agent skills

Copy the folders into wherever your agent reads skills from, e.g.:

```bash
cp -r skills/* ~/.claude/skills/        # Claude Code
cp -r skills/* ~/.pi/agent/skills/      # Letaido
```

Most environments load skills at session start, so start a fresh session afterwards.

## License

MIT — see [LICENSE](LICENSE).
