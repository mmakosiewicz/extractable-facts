---
name: query-match-audit
description: "Check whether a page or draft actually matches the queries and AI prompts you want it to win, and whether it offers anything worth retrieving instead of a generic summary. Flags weak titles and meta descriptions, answers buried inside a broader page, thin sections, topic-coverage gaps, vague claims, missing evidence, weak examples, and unsupported appeals to authority — with a concrete fix for each. Works on a live URL or an unpublished draft (.md/.docx/.txt), for any brand. Use when someone asks 'does this page target the right query', 'why isn't this ranking or getting cited for X', 'is this content good enough / too generic / too thin', 'should this be its own page or a section', 'do we need a comparison page for X vs Y', 'what would make this worth citing', 'audit this content against these prompts', or wants a pre-publish relevance check. With product docs, customer research, or support conversations supplied, it also identifies what distinctive material could be added. It cannot invent original data, customer insight, or product facts — those come from the team. NOT for whether AI can mechanically extract facts from the page (that's an extractability audit), NOT for keyword research or picking targets, and NOT for measuring existing AI visibility."
---

# Query Match & Content Substance Audit

Two questions, in order. A page has to pass the first to have a shot at the second:

1. **Does this page obviously match what the user is asking?** Clear from the title, meta description, headings, URL, and body — not buried three-quarters of the way down a broader page.
2. **Is there anything here worth retrieving?** Generic summaries are easy to replace. If dozens of pages say essentially the same thing, an AI system has no reason to use yours.

The first question is usually the bigger lever and the cheaper fix. A brilliant section buried inside a page about something else loses to a mediocre page that's *about* the query.

**What this skill cannot do:** invent real expertise, original data, customer insight, or facts about your product. It can tell you a section is generic and name exactly what kind of material would fix it; it can't manufacture that material. Those inputs come from the team. Give it access to product documentation, customer research, or support conversations and it will find the specific opportunities — that's the difference between "add an example here" and "your support queue has eleven questions about this; three of them belong in this section".

---

## Before you start: what are you targeting?

**This audit is meaningless without target queries.** They're the yardstick. If the user hasn't supplied them, ask — one question, then proceed.

Good targets are the actual prompts or searches you want the page to win: `ai visibility tools for startups`, `notion vs obsidian for research`, `how do I export my data from <product>`. Ask for 3–10. If they only have a topic, help them phrase 3–5 concrete queries from it and state what you assumed.

Also worth knowing, though don't stall on it:

- **Branded or unbranded?** Branded prompts ("is <product> any good", "<product> vs <competitor>", "does <product> do X") are markedly easier to win with a dedicated page, because few pages compete for them and relevance carries most of the weight. Unbranded commercial queries are contested, so substance matters more.
- **Which surface?** Products leaning on search infrastructure (Google AI Overviews and AI Mode, Copilot, Perplexity) inherit search's quality bar, so distinctiveness and sourcing count heavily. Assistants like ChatGPT weight it differently. If the user names a target surface, say how that shifts the advice.

---

## Workflow

### 1. Run the deterministic pass

```bash
python3 scripts/querymatch.py --url https://example.com/post/ \
    --queries "ai visibility tools for startups" "best ai visibility tools"

python3 scripts/querymatch.py --draft ./article.md --queries-file ./prompts.txt --json /tmp/qm.json
```

`--queries-file` takes one query per line; `#` comments are ignored. `.docx` drafts work directly.

It reports, per query:

| Verdict | Meaning |
|---|---|
| **dedicated page** | Title and/or H1 substantially covers the query — this page is *about* it |
| **dedicated section** | Not in the title, but a heading addresses it squarely |
| **buried in body** | The terms appear, but nothing signals the page answers this |
| **not covered** | The page doesn't address it |

Plus per-field coverage (title / H1 / slug / headings / body), which terms are missing from the title, and how deep into the page the query's terms first co-occur.

And for substance: which of nine hard-to-reproduce signals are present or absent (original data, methodology, firsthand experience, examples, screenshots, benchmarks, customer insight, expert input, workflows), figures per 1,000 words, external sources, generic openers, thin sections, and unsupported appeals to authority ("studies show" with no link).

The script counts and pattern-matches. **It cannot tell whether an example is any good** — only whether one exists. Treating the signal count as a score is how this audit goes wrong.

### 2. Decide dedicated page vs section

For each query the script marks as `buried in body` or `dedicated section`, make a call: does this deserve its own page?

Arguments for splitting it out:

- The query is **commercially important** — a comparison, an alternatives page, a use case, a specific integration, a market or industry variant.
- The query has its **own intent** that the host page's title doesn't promise. A reader searching it would feel the current page is mostly about something else.
- There's enough distinctive material to fill a real page. **A thin page created purely to match a query is worse than a good section** — it fails question 2 and the whole thing was for nothing.

Arguments against:

- It's a natural subtopic a reader expects to find in the broader piece.
- You'd be duplicating the host page with a different title. Two near-identical pages compete with each other and dilute both.

These query families almost always justify a dedicated page: **`X vs Y` comparisons**, **`alternatives to X`**, **per-use-case pages**, and **per-industry or per-market variants** of a page that already works. Comparison and alternatives pages in particular are the reliable way into branded conversations — relevance does most of the work, because the field is thin.

When you recommend a split, specify: the proposed title, the H1, the URL slug, which sections move across from the host page, and what needs writing from scratch. A recommendation to "create a dedicated page" without those is a to-do, not a plan.

### 3. Fix the match signals

For queries the page *should* own, check each surface and propose the rewrite:

- **Title** — the strongest signal. If the script lists terms missing from the title, that's usually the highest-value edit on the page. Propose the actual replacement title, keeping it readable; a keyword-stuffed title that reads badly is a different failure.
- **Meta description** — should state what the page answers, not tease it. Rewrite it in full; don't describe what it should say.
- **H1** — normally matches the title's promise.
- **Headings** — at least one heading should address the query in the user's own words. Question-form headings work well for question-form prompts.
- **Slug** — worth flagging on a draft, where it's free to change. On a live page, only recommend a URL change when the gain clearly beats the redirect cost — say so explicitly rather than recommending it blind.
- **Depth** — if the query's terms first co-occur at 60% depth on a page that should own it, the answer is too late. Hoist it.

### 4. Judge substance

Read the page. The script tells you which signals are *missing*; you decide whether that matters here and what would fix it.

**The replaceability test:** if a competitor wrote this page from the same three sources in an afternoon, it's replaceable. What's in here that nobody else could have written? If the answer is nothing, that's the finding, and it outranks every heading tweak in the report.

What tends to stand out, roughly in order of how hard it is to copy:

| Material | Why it's hard to reproduce |
|---|---|
| Original data, tests, benchmarks | Requires doing the work |
| Customer insight, support patterns | Requires having customers |
| Firsthand experience of the process | Requires having done it |
| Original screenshots, worked examples | Requires access and effort |
| Clear methodology and caveats | Requires rigor, and signals it |
| Expert judgment, a defended position | Requires a view worth defending |

**Be specific about what's missing.** "This section is thin" is useless. "This section claims the setup is straightforward but never shows it — a screenshot of the actual configuration screen and the three fields that trip people up would make it unreproducible" is actionable.

**Thin sections:** the script flags sections under 120 words (excluding template chrome in URL mode). Judge each one — some short sections are correctly short. A thin section on a *core* subtopic is a coverage gap; a thin section on a peripheral one is fine.

**Unsupported claims:** "studies show", "experts agree", "most companies" with no link. Each is both a credibility problem and a missed extractability opportunity — there's nothing specific for a retriever to match. List them with the question that would resolve each.

**Topic coverage:** what would a reader searching this query expect that the page doesn't cover? Compare against the top-ranking pages if you can reach them; otherwise reason from the query's intent. Name the missing subtopics as proposed headings, not as a vague gap.

### 5. Mine internal knowledge, if you have access

When the user has supplied product documentation, customer research, support conversations, sales-call notes, or internal data, this becomes the most valuable part of the audit. Look for:

- **Questions asked repeatedly in support** that the page doesn't answer — each is a heading with a real answer already attached.
- **Product facts contradicting the page** — outdated limits, renamed features, changed pricing. Flag these hard; a wrong fact confidently stated is worse than a missing one, and AI systems will repeat it.
- **Real numbers that could replace vague claims** — usage data, benchmarks, results.
- **Customer language** differing from the page's language. If customers say "seat" and the page says "license", the page misses the query.
- **Genuine differentiators** stated nowhere on the page.

Cite where each came from so the author can verify it. And apply the same rule as everywhere else: **use what the source says, not what it implies.**

### 6. Write the report

Every finding carries its fix, spelled out. Not "the title could be stronger" — the proposed title, written.

```
## Verdict
One paragraph per target query: does this page match it, and is there anything
here worth retrieving. Name the single biggest lever.

## Query match
A row per target query: verdict, what's missing, the proposed fix.

| Query | Verdict | Fix |

## Recommended new pages
Only where a split is genuinely warranted. Each with: proposed title, H1, slug,
what moves across, what needs writing.

## Substance
What makes this page hard to replace, and what doesn't. Be direct when the
honest answer is "nothing yet".

## What to add — and who has to supply it
Specific material that would make this page distinctive, each tagged with what
kind of input it needs: original data / a customer example / a screenshot /
a product fact / an expert view.

## Fix now
Title, meta, headings, thin sections — the edits that need no new information.
```

Split the last two deliberately. "Fix now" is everything actionable today; the section above it is the team's homework. Blurring them lets the easy edits hide the fact that the page still isn't worth citing.

Be honest in the verdict. If a page matches its query perfectly and still has nothing distinctive, say so — the fix is new material, not another heading pass.

---

## Delivering it

Write the audit as a page the user can return to, and link it in your reply. For multiple pages against the same query set, one report with a summary table beats separate ones.

For a draft, offer to apply the no-new-information fixes directly to the file so the user can diff them. Ask first.

## Scope boundaries

- **Whether AI can mechanically extract facts from the page** (chunking, standalone passages, entity density) → an extractability audit; the natural companion to this one
- **Picking which queries to target** → keyword or prompt research
- **Where the brand already appears in AI answers** → an AI visibility or mention-gap audit
- **Whether crawlers can reach the page** → a crawl/access audit
- **House voice and formatting** → the brand's style guide
- **Inventing expertise, data, or product facts** → not this skill, not any skill. The team supplies those.
