# Make facts and data easy to extract for AI

AI search engines don't read a page top to bottom. They split it into chunks, retrieve the passages most relevant to a query, and cite only the fragments that support an answer.

So a page can be well written, accurate, and thoroughly researched, and still never get cited — because its best facts are buried late, hedged into mush, or written so they collapse when lifted out of context.

This repo holds two agent skills for fixing that. The first audits a page or draft for extractability and hands back a rewrite for every problem it finds. The second is the editorial craft layer underneath it — the prose rules that make content worth citing in the first place.

None of this means writing robotic "LLM-friendly" copy. It's mostly good editorial hygiene: make the answer easy to find, keep claims precise, put important information in visible text, and make sure key passages still make sense when read on their own.

| Skill | What it does |
|---|---|
| [`ai-extractability-audit`](skills/ai-extractability-audit) | Audits a live URL or an unpublished draft for whether AI search engines can extract and cite its facts. Returns a fix list with a concrete rewrite for every finding. |
| [`blog-style-editing`](skills/blog-style-editing) | Edits blog and article prose to a high editorial standard — voice, structure, headings, AI-tell removal. Adapts to whatever house style you give it. |

Both are brand-neutral. Neither asks you to mention any product.

They're in the [Agent Skills](https://code.claude.com/docs/en/skills) format (`SKILL.md` + optional `scripts/` and `references/`), so they work in any agent environment that reads skill folders — Claude Code, Letaido, Codex, ChatGPT Agents. You can also run the audit script directly and ignore the agent part.

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

### The script is only half of it

`extractability.py` counts and pattern-matches. **It over-flags on purpose** — it's cheap to run and catches candidates. The `SKILL.md` then directs the judgement pass an agent (or you) performs over the flagged chunks:

- Which hedges are *unnecessary* (evidence supports a firm claim) versus *honest uncertainty* (leave them — stripping a legitimate hedge manufactures a false claim)
- Which passages would actively **mislead** if quoted alone. A caveat paragraph retrieved on its own can read as the main finding. This is the highest-severity finding in the audit.
- Which specific entities are missing — "which five systems? which year?" beats "add more specifics"
- Which format suggestions are genuine

Treating the script's raw output as the finding is the main way this audit goes wrong.

### The hard boundary

**The skill never decides whether a claim is true.** Every rewrite must trace to a source the user supplies or the page already cites. Unsourced claims go in a "Needs a source" section with a specific question attached, rather than being confidently restated. Turning a hedge into a definitive statement without evidence doesn't improve the page — it manufactures a false claim that AI systems may then repeat.

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

## Both skills return rewrites, not observations

Every finding arrives with the replacement text, quoted as current versus proposed. "This paragraph is too long" is an observation; "split after '…ranking factor.'" is a fix. Phrasings like "consider adding specifics" or "could be tightened" are explicitly banned in both skills.

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
