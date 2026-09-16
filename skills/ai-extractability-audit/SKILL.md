---
name: ai-extractability-audit
description: "Audit any page or draft for whether AI search engines can extract, understand, and cite its facts, and return a fix list with a concrete rewrite for every finding — answer position, entity density, hedged claims, passages that stop making sense when quoted out of context, weak headings, table/FAQ/definition opportunities, and facts that exist only in structured data. Works on a live URL or an unpublished draft (.md/.docx/.txt), for any website, blog, or brand. Use when someone asks to 'optimize this for AI search / ChatGPT / LLMs', 'make this page easier for AI to cite', 'will AI quote this', 'is my content chunk-friendly', 'find vague or buried claims', 'check what an AI bot can see on this page', 'why isn't AI citing us', 'GEO/AEO audit this page', or wants a pre-publish extractability check on a draft. Also covers rewriting flagged passages into self-contained statements — but only from sources the user supplies; it never decides whether a claim is true. NOT for measuring where a brand already appears in AI answers (that's an AI visibility or mention-gap audit), NOT for crawlability and indexing setup, and NOT for house voice or tone."
---

# AI Extractability Audit

AI search engines don't read a page top to bottom. They split it into chunks, retrieve the passages most relevant to a query, and cite only the fragments that support an answer. A page can be well written, accurate, and thoroughly researched, and still never get cited — because its best facts are buried late, hedged into mush, or written so they collapse when lifted out of context.

This skill finds those failures **and proposes the specific fix for each one**. The deliverable is an actionable rewrite list, not a diagnosis — every finding arrives with replacement text the user can accept, reject, or paste in. Two modes, same analysis:

- **URL mode** — a live page. Adds the visibility layer: what a crawler actually receives, and which facts exist only in structured data.
- **Draft mode** — an unpublished `.md`, `.txt`, or `.docx`. Everything except the crawl layer, so problems get fixed before publish.

**The hard boundary:** this skill flags weak, vague, and non-standalone passages, and rewrites them when given evidence. It cannot decide whether a claim is *true*. Every rewrite must trace to a source the user supplies or the page already cites. An unsourced claim gets flagged for the human — never confidently restated. Turning a hedge into a definitive statement without evidence doesn't improve the page; it manufactures a false claim that AI systems may go on to repeat.

**It is also not a product-placement tool.** Extractability is about whether a machine can lift a fact out of the page. Nothing here asks the writer to mention any product, the site's own tools, or a sponsor. If the audit recommends adding a specific name or number, it's because the passage makes a claim that needs an identifiable subject — not because a brand should appear.

## What the research says

Three findings anchor the thresholds. Cite them when explaining a recommendation, and re-check them — they're empirical and will date:

- **44.2% of AI citations come from the first 30% of a page** (Kevin Indig's citation research). Position matters far more than most writers assume.
- **Cited passages use definitive language over hedging, and carry substantially more named entities than typical prose.** Entity density is a citation lever, not a style preference.
- **Five major AI systems ignored JSON-LD, hidden Microdata, and hidden RDFa, relying on visible HTML instead** ([Ahrefs test, 2026](https://ahrefs.com/blog/schema-ai-citations/)). A fact that lives only in structured data is a fact AI search doesn't have.

None of this means writing robotic "LLM-friendly" copy. It's editorial hygiene: make the answer easy to find, keep claims precise, put important information in visible text, and make sure key passages still make sense read alone.

---

## Before you start: whose page is this?

Two things to establish, because both change the recommendations:

**1. The page's question.** Name the *one question this page exists to answer*. Get it from the user, or infer it from the title and H1 and state your inference so they can correct it. Every later judgement — is the answer early enough, does this heading state something — depends on knowing what the answer is supposed to be. Skipping this produces a generic report that reads like a linter.

**2. The house style, if there is one.** Heading conventions vary: some sites use sentence case, some Title Case, some run questions as H2s. The script reports Title Case headings as a flag because sentence case is the more common convention, but **if the site's style is Title Case, ignore that flag** — say so in the report rather than recommending a change that contradicts their guide. Ask, or infer from the surrounding pages. If a separate house-style skill or guide exists for this brand, defer to it on anything cosmetic; this skill's authority stops at extractability.

Never import one brand's conventions into another brand's audit.

---

## Workflow

### 1. Run the deterministic pass

```bash
python3 scripts/extractability.py --url https://example.com/post/
python3 scripts/extractability.py --draft ./article.md --json /tmp/audit.json
```

`.docx` drafts work directly (Word heading styles become markdown headings). Add `--json` when you want the full per-chunk data for the next step. The script has no dependency on any particular CMS, platform, or brand — it takes HTML or markdown and counts.

It reports:

| Section | What it tells you |
|---|---|
| Early zone | Chunk count, word count, and entity density in the first 30% |
| Headings | Which ones name a topic without stating anything, which run long, which are Title Case |
| Flagged chunks | `not-standalone`, `hedged`, `low-entity-density` — indices to hand to the judgement pass |
| Format opportunities | Where a table, definition, list, or FAQ would beat the paragraph |
| Visible vs structured | URL mode only: facts present in JSON-LD but absent from visible text |
| Worst chunks | Ranked by flag count, with the offending text |

The script is deliberately mechanical — it counts and pattern-matches. It will over-flag. Treating its output as the finding is the main way this audit goes wrong.

### 2. Judge the flagged passages

Read the flagged chunks yourself and decide which flags are real. This is the step that makes the audit worth reading.

**Answer position.** Where does the direct answer to the page's question appear, as a % of depth? If it's past 30%, say what sits in front of it and whether that preamble earns its place. A definition the reader needs first is fine; three paragraphs of context-setting is not.

**Hedged claims.** Separate the two kinds:
- *Unnecessary hedging* — the evidence supports a firm statement but the prose waffles. Rewrite to the definitive form.
- *Honest uncertainty* — the evidence genuinely is mixed. **Leave it.** Stripping a legitimate hedge turns a careful claim into a false one. Say in the report that you left it and why.

**Standalone failures.** For each flagged chunk, read it as if it were the only thing an AI retrieved. Does it still mean what the author intended? Common breaks: opening pronouns with no antecedent, "as mentioned above", ordinals with no local list, and — the dangerous one — a passage whose meaning *inverts* without its neighbours. A caveat paragraph quoted alone can read as the main finding. Flag those as **misleading-when-quoted**, the highest-severity finding in this audit.

**Entity density.** Low density on a transitional paragraph is fine. Low density on a passage making a substantive claim is a problem: the claim has no names, numbers, dates, or sources attached, so there's nothing for a retriever to match on and nothing to make the passage verifiable. Name the specific missing entities — "which five systems? which year? how many pages?" — rather than saying "add more specifics".

Entities means anything identifiable: people, organizations, products, places, dates, figures, standards, methods, named sources. Whose products is irrelevant. A page about a competitor's tool is more extractable when it names that tool precisely.

**Headings.** A heading that names a topic ("Background", "Pricing") tells a retriever nothing. A heading that states the answer ("Schema markup didn't move AI citations") is itself a citable fact and a retrieval anchor. Propose rewrites for the topic-label-only ones, in the site's own heading convention.

**Format opportunities.** Confirm each suggestion is genuine. Four figures in a paragraph *usually* wants a table; sometimes it's a narrative where the numbers belong in prose. Say which you'd actually change.

### 3. Check what the bot can see (URL mode)

The `visible vs structured` section lists facts found in JSON-LD but not in visible text. Each one is a fact AI search doesn't have. Pricing, feature lists, ratings, availability, and author credentials are the usual casualties.

Two more signals: no `<article>` or `<main>` wrapper often means readability extractors mangle the page — worth verifying by comparing what a readability extraction returns against the full page, since some templates lose every heading. Zero tables on a page full of comparisons is a missed extraction aid.

For deeper crawl-layer questions — robots.txt, noindex, bot blocking, per-crawler access — that's a different job; this skill assumes the page is reachable.

### 4. Write the report

**Every finding you keep must arrive with a proposed rewrite.** The user should be able to act on the report without asking a single follow-up question — read it, accept or reject each suggestion, paste it in. A finding without a rewrite is an observation, and observations are not what anyone commissions an audit for.

Three things make a finding actionable, and all three are required:

- **Location** — chunk index and heading, or a quoted fragment the user can search for.
- **Why it hurts** — in retrieval terms, one sentence. Not "this is vague" but "quoted alone, this passage doesn't say which study".
- **The rewrite itself** — the actual replacement text, quoted. Never "consider adding specifics", "could be tightened", or "you may want to restructure this". If you can write the fix, write it.

The only findings that may lack a rewrite are those in **Needs a source** — and those still need a specific question ("which five systems, and in what year?"), not a vague gesture at missing evidence.

Order by severity: misleading-when-quoted first, then answer position, then everything else.

Structure:

```
## Verdict
One paragraph: can AI extract and cite this page's key facts, and what's the single
biggest obstacle.

## Fix first
The 1-3 highest-impact findings, each with its rewrite spelled out in full.

## Full findings
Every remaining finding, by category (answer position / standalone / hedging /
entities / headings / format / visibility). Each one still gets a rewrite — these
are lower impact, not lower effort. A table works well:

| # | Where | Problem | Proposed rewrite |

## Left alone deliberately
Flags the script raised that you judged fine, and why. This is not filler —
it stops the next person re-litigating the same passages.

## Needs a source
Claims you could sharpen but won't without evidence, each with the specific
question the user needs to answer.
```

For a longer page, a rewrite table beats prose — it lets the user scan current-versus-proposed and accept in bulk.

**Before sending, re-read your own report and check every finding has a rewrite or a specific source question.** If any item reads as "here's a problem, good luck", fix it or drop it.

### 5. How to write the rewrites

Rewrites are part of the report, not a follow-up service. Propose them by default; applying them to a file is the separate step that needs the user's go-ahead.

A good rewrite is **minimal, sourced, and in the author's voice.** Change the words that cause the retrieval failure and nothing else — a six-word fix the author accepts beats a rewritten paragraph they argue with. Show it as current versus proposed so the delta is visible.

Apply these patterns, each conditional on having a source:

| Problem | Rewrite pattern |
|---|---|
| Buried answer | Hoist it into the first paragraph under the relevant heading; keep the detail below it |
| Vague claim | Attach the specific entity: who, what number, which year, which product, which source |
| Hedged with evidence | State it definitively: "may reduce" → "reduced X by N% in [study]" |
| Hedged without evidence | Leave it. Flag it under "Needs a source" |
| Orphan pronoun | Replace with the noun it refers to |
| Back-reference | Restate the referenced point in one clause |
| Topic-label heading | Rewrite so the heading states the section's answer |
| Comparison prose | Convert to a table with named rows |
| Buried definition | Move it to the section's first sentence, in `[Term] is [definition]` form |
| Schema-only fact | Add it to visible copy; keep the structured data as well |

**Worked example of the expected shape:**

> **Chunk 4 (81% depth), "How your AI agent can help" — orphan opener**
>
> Current: "This is a good first job for an agent: mechanical, repetitive…"
>
> Why it hurts: "This" points at a task described two paragraphs earlier under a different heading. Retrieved alone, the passage never names what the job is.
>
> Proposed: "Checking crawler access is a good first job for an agent: mechanical, repetitive…"

Six words changed, subject now local to the chunk, voice untouched. That is the target shape for every finding.

Keep the author's voice. An edit that reads like a different person wrote it is a failed edit, however extractable it is. Match the publication's conventions, not your own defaults.

---

## Delivering it

An audit is a deliverable: write it as a page the user can find and return to, and link it in your reply. If they want a visual — per-chunk depth vs flags, entity density across the page — that's a separate artifact, not a section of the report.

For a draft, offer to apply the rewrites directly to the file as a second pass, so the user can diff it. Ask first — the report proposes, the user disposes.

## Scope boundaries

- **Where a brand already appears in AI answers** (mentions, share of voice, citation gaps) → an AI visibility or mention-gap audit
- **Which cited pages have gone stale** → a citation freshness audit
- **Crawlability, indexing, bot access** → a crawl/access audit
- **House voice, tone, and publishing format** → the brand's own style guide or style skill
- **Whether a claim is true** → not this skill, not any skill. A human with a source.
