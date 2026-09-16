---
name: blog-style-editing
description: "Edit or write blog and article prose to a high editorial standard — voice, sentence and paragraph discipline, heading conventions, intro and conclusion structure, definition/explanation/answer patterns, link and citation formatting, and cutting AI-sounding writing. Works for any brand or publication; adapts to the house style you give it. Use when someone asks to 'edit this draft', 'tighten this article', 'make this read better', 'apply our style', 'does this match our voice', 'fix the headings', 'make this sound less like AI', 'copy-edit this post', or wants a style review before publishing. Load a brand profile from references/ when one exists for that publication. NOT for deciding what to write about (keyword research, outlining, topic gaps), NOT for fact-checking or sourcing claims, and NOT for whether AI search can extract the page's facts (that's an extractability audit)."
---

# Blog Style Editing

Editorial craft rules for blog and article prose: how sentences, paragraphs, headings, and structure should work. This covers **language and formatting only** — not what to write about, not research, not fact-checking.

The rules below are general craft, not one brand's preferences. They hold for most business and technical blogs. Where a publication's own guide disagrees, **the publication wins** — see "Working with a house style" below.

If you're editing an existing draft, don't rewrite wholesale. Fix what actually violates a rule and leave the author's voice alone — an edit that reads like a different person wrote it is a failed edit.

---

## What to hand back

Two jobs, and the user usually wants the second:

**A style review** — findings about the draft. **Every finding must carry the replacement text**, quoted as current versus proposed. "This paragraph is too long" is an observation; "split after '…ranking factor.' and start the next paragraph at 'But'" is a fix. Never hand back "consider tightening this", "could be more specific", or "you may want to vary sentence length" — if you can see the problem you can write the fix, so write it.

**An edited draft** — the rewrites applied to the file. Offer this whenever you've reviewed something; ask before overwriting so the user can diff.

Order findings by how much they cost the reader, not by how easy they are to spot. A buried thesis outranks twelve heading-case violations. Group the mechanical fixes (case, spelling, contractions) into one line rather than listing each — they're a find-and-replace, not twelve decisions.

Two things that stay as flags rather than rewrites, because guessing does real damage:

- **A missing example or statistic.** Name the gap and ask for the fact. Never invent one.
- **A claim you can't verify.** Flag it for the author; don't rephrase it into something that sounds more confident.

Before sending, re-read your review: if any item tells the author there's a problem without telling them what to write instead, it isn't finished.

---

## Working with a house style

Before editing, establish whose style applies:

1. **The user names a brand profile** → read `references/<brand>-profile.md` if it exists and let it override anything below.
2. **The user supplies a style guide** → that guide wins on every conflict. Follow it.
3. **Neither** → use the defaults below, and flag the conventions you assumed (heading case, person, word count) so the user can correct them in one pass rather than twenty.

Conventions that genuinely vary between publications, and which you should never silently impose:

| Convention | Common variants |
|---|---|
| Heading case | Sentence case / Title Case |
| Person | First person singular / first person plural / third person |
| Spelling | American / British |
| Contractions | Allowed / avoided in formal or enterprise contexts |
| Em-dash spacing | Spaced / unspaced / avoided entirely |
| Oxford comma | Used / not used |
| Product mentions | Encouraged / restricted / banned outright |

Bundled profiles: `references/ahrefs-profile.md` (the Ahrefs blog). Add more as they come up.

---

## Voice and tone

Write like you're explaining something to a smart colleague who's busy. Not lecturing, not dumbing down.

- **Consistent person.** Pick first or third and hold it across every section. Mixed person is the most common sign of a multi-author or AI-assisted draft.
- **Direct.** Say the thing. "Here's the thing:" occasionally is fine; three times in one article is a tic.
- **Take a position** where the evidence supports one. Hedging everything is worse than being wrong, and unfalsifiable prose is unmemorable prose.
- **Humor is dry and situational**, never forced, and it's optional — some publications don't want it at all.
- **No corporate speak** — leverage, synergize, cutting-edge, industry-leading, best-in-class, seamless, robust, holistic, unlock, empower.
- **No hype adjectives** — revolutionary, game-changing, amazing, exciting, groundbreaking, mastery of. If something genuinely is a big deal, show the number instead of reaching for the adjective.
- **No unearned urgency** — "in today's fast-paced world", "now more than ever", "the landscape is changing".

### AI-tell patterns to cut

These read as machine-written even when the content is good. Cut them on sight:

| Pattern | Why it's out | Fix |
|---|---|---|
| "It's not X, it's Y" | The signature AI contrast pivot | Just say Y |
| "Not 'less of you' — nothing" | Negation-then-correction, same family | State the point once |
| "X, but not Y" where X already implies it | Redundant pivot | Drop the clause |
| "This isn't theoretical" / "This isn't just a theory" | Announces credibility instead of showing it | State the claim and the proof |
| "If you're new to X… If you're already doing X…" | Dual-audience hedge | Pick one reader or write neutrally |
| Em-dash used for a contrast pivot mid-sentence | Substitutes punctuation for an argument | Fine for parentheticals; not as "actually, here's the real point" |
| "In this article, we will…" | Formal throat-clearing | Say what they'll get, conversationally |
| "If you've ever wondered…" | Throat-clearing hook | Open on the claim |
| "Let's dive in" / "Let's explore" | Filler transition | Start the section |
| Tricolon everywhere ("clear, concise, and compelling") | Rhythm on autopilot | Keep one, cut two |

Rhythmic lists ("No X, no Y, no Z") used deliberately are **fine** — that's prose rhythm, not the contrast tic.

---

## Sentences and paragraphs

- **One thought per sentence.** Two ideas joined by "and" or a semicolon are usually two sentences.
- **Max 3 lines per paragraph** for web reading. Long paragraphs kill scannability.
- **Simple words.** "Seen" not "misconstrued". "Use" not "utilize". "Because" not "due to the fact that".
- **Cut fluff.** Throat-clearing, restating the heading, and "as we all know" all go.
- **Vary sentence length.** All-short reads staccato; all-long reads like a filing.
- **Break up long stretches** with an image, blockquote, list, table, or bolded line every 3–5 paragraphs.

---

## Headings

- **H2 for major sections, H3 for subsections.** Deeper levels sparingly.
- **Case follows the house style** — sentence case is the more common web convention, but confirm rather than assume.
- **One point per heading.** Not "What is X, why it matters, and how to do it" — that's three headings.
- **Under 15 words.**
- **Specific and benefit-driven** — "Optimize your pin titles" beats "Titles".
- **State something.** A heading that names a topic ("Background") carries no information; one that states the section's point does, and doubles as a retrieval anchor for AI search.
- **Never place two headings back-to-back.** Always put intro text between a heading and its first subheading.
- **Skim test:** a reader who reads only the headings should understand the article's value.

---

## Article structure

### Introduction — under 100 words

**PAS** is the reliable default: Problem → Agitate → Solution.

1. **Problem** — state the pain point.
2. **Agitate** — why it matters, or what happens if ignored.
3. **Solution** — preview what the article delivers.

> Most websites get zero traffic from Google. That's not an exaggeration — 96.55% of pages get no organic search traffic at all. But it doesn't have to be that way. In this guide, I'll show you exactly how to do SEO in 2026, step by step.

Open on a hook: a bold claim, a surprising result, a real personal action, or a myth to debunk. No generic topic overview.

**Write the intro after the body sections** — you only know what the article actually covers once it exists.

### Body sections — inverted pyramid

Every section leads with the **BLUF** (Bottom Line Up Front): the essential point in the first 1–2 sentences, then supporting detail.

Preferred section pattern: **Claim → Evidence → Interpretation → Practical advice.**

Transition between sections naturally. Never "Moving on to…" or "Let's now look at…".

**Later sections must be as rich as early ones.** If section 9 feels thinner than section 1, that's the single most common quality failure in long drafts. Fix it by adding one of: a specific data point, a counterargument and response, a "here's what this means in practice", a common mistake to avoid, or a worked example.

### Conclusion — under 150 words

Two jobs:

1. Summarize the core takeaway.
2. Give one actionable next step or extra insight (the "souvenir" — something the reader takes away beyond the summary).

End with whatever CTA the publication uses. Don't invent one.

---

## Prose patterns

### Definitions

Format: `[Term] [abbreviation if needed] [conjunction] [definition in 1–3 sentences]`

> **What is bounce rate?**
> Bounce rate is the percentage of visitors that take no further action after landing on a webpage, like clicking through to another page, leaving a comment, or adding an item to their cart.

Put the definition in the section's **first** sentence, not buried mid-paragraph. Expand below it if more is needed.

### Explanations — always what AND why

> Install an image compression plugin like ShortPixel. This reduces file sizes without visible quality loss, which improves page speed — a confirmed Google ranking factor.

Not:

> ~~Install an image compression plugin.~~

### Answers to questions

Format: `[Part of question] [conjunction] [brief answer]. [Further explanation]`

> **Why is SEO important?**
> SEO is important because higher rankings usually lead to more organic traffic. This is because 65.9% of searchers click one of the top three organic results.

Don't force this shape if it reads unnaturally.

### Examples — one per major point

Every major claim needs a concrete illustration: specific, relevant, and real. Real numbers, real names, real timeframes. A vague example is worse than none.

> Backlinks don't last forever. We lost 847 referring domains in the past 7 days alone — that's just how the web works. Old pages get deleted, sites shut down, and webmasters change their minds.

**Never invent an anecdote or a statistic to satisfy a style rule.** If the draft needs an example and you don't have a real one, flag the gap for the author. A fabricated "in our testing we found…" is a far worse defect than a thin paragraph.

---

## Links and citations

Link the **specific claim**, not the whole sentence.

| Do | Don't |
|---|---|
| `Pinterest has over [450 million monthly active users](url).` | `[Pinterest has over 450 million monthly active users.](url)` |
| `processes over [5 billion searches](url) per month` | `[processes over 5 billion searches per month](url)` |

- **Statistics** → link the number.
- **Quotes** → link the attribution: "As [Google's John Mueller](url) put it…"
- **Best practices** → link the recommendation: "Pinterest recommends a [2:3 aspect ratio](url)".
- **One source per claim.** Don't over-link.
- **Link the primary source**, not an aggregator's summary of it, wherever you can reach it.
- Prefer sources from the last 2 years unless the claim is genuinely historical.

---

## Images and visuals

Mark where a visual belongs inline, in the draft:

- `[SCREENSHOT: Description of what to show]`
- For a tool screenshot, name the exact path: `[SCREENSHOT: Site Explorer > Backlinks report for example.com]`
- For a custom graphic: `[ILLUSTRATION: Flowchart showing X → Y → Z]`

**Alt text** on every real image: simple, descriptive, roughly 5–12 words, no "image of" prefix, no keyword stuffing. Purely decorative images get `alt=""`.

---

## Mentioning products and tools

This applies whether the product is the publisher's own, a competitor's, or a third party's.

**The test is whether the reader needs it to do the thing the section is about.** If the section explains how to check backlinks, naming a tool that checks backlinks helps. If it doesn't, the mention is an ad.

- **No mention quota.** Zero product mentions in an article is a perfectly good outcome. Never insert one to hit a target.
- **Never imply one product is the only way** to solve the problem.
- **Name competitors plainly** where they're the right answer. Evasive "some tools offer…" phrasing reads as promotional and is less useful to readers *and* less extractable for AI search, which has nothing specific to match on.
- **Show the path, not the pitch:** "go to X, enter your domain, check the Y report" beats "X is the industry's leading solution for Y".
- If the publication has a mention policy, follow it — that's a business decision, not a craft one. Check the brand profile.

---

## Length

- **As short as possible while still complete.** Never pad to hit a count.
- Cut details only 1% of readers care about.
- Weight sections by importance: core value sections (the tips, the how-to, the analysis) should be 60–70% of the total; intro, definitions, and conclusion 30–40% combined.
- If the publication sets a target range, use it. Absent one, let the topic decide.

---

## Pre-publish checklist

| Check | Requirement |
|---|---|
| Examples | Every major point has a specific, real example |
| Voice | Consistent person throughout, consistent across sections |
| Opinions | A clear stance where evidence supports one |
| Fluff | No throat-clearing, no filler, no restated headings |
| AI tells | No contrast pivots, no "this isn't theoretical", no dual-audience hedges |
| Paragraphs | Max 3 lines each |
| Headings | House case, under 15 words, one point each, none back-to-back, each states something |
| Language | No corporate speak, no hype adjectives, no unearned urgency |
| Product mentions | Only where genuinely useful; no quota met for its own sake |
| Links | Wrap the specific claim; primary sources |
| Alt text | Present on every real image |
| Length | Nothing padded |
| Intro | Under 100 words, hooks, written after the body |
| Conclusion | Under 150 words, has a souvenir |
| Consistency | Section 9 as rich as section 1; terminology consistent |
| Fabrication | No invented anecdotes, statistics, or quotes |

---

## Bundled references

- `references/ahrefs-profile.md` — the Ahrefs blog: its voice specifics, product-mention guidance, CTA convention, and a pointer to its WordPress shortcode set. Load only when editing for that publication.
- `references/wordpress-shortcodes.md` — the Ahrefs blog's WordPress shortcode markup and publishing workflow. Brand-specific; irrelevant to other sites.
