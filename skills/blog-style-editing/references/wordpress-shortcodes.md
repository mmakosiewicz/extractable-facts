# Ahrefs WordPress shortcodes

Reference for turning a finished markdown draft into a WordPress-ready document. Use only on **finished** articles — real embedded images, not `[SCREENSHOT: ...]` placeholders, unless you're deliberately leaving placeholders for a designer.

Shortcodes must reach WordPress **literally**. If any markdown → HTML pass escapes `[` or `]`, the shortcodes break. Check the output before pushing.

---

## Shortcode set

### Content structure

| Shortcode | Purpose | When to use |
|---|---|---|
| `[intro_text][/intro_text]` | Wraps the intro paragraph | First paragraph after the title |
| `[intro_toc]` | Auto-generates table of contents | After the intro, before the first H2 |
| `[post_nav_link]` | Section navigation anchor | Wraps every H2 heading |

### Callouts

| Shortcode | Purpose | When to use |
|---|---|---|
| `[recommendation title="Tip"][/recommendation]` | Highlighted tip box | Actionable advice, tool recommendations |
| `[sidenote][/sidenote]` | Side note callout | Tangential but useful info |
| `[editor_note][/editor_note]` | Editor attribution | Editorial comments or update notices |

### Quotes, media, end matter

| Shortcode | Purpose | When to use |
|---|---|---|
| `[blockquote]` | Styled quote with author | Expert quotes, testimonials |
| `[caption][/caption]` | Image with caption | Any image needing context |
| `[toolWidget]` | Ahrefs free-tool embed | When referencing an Ahrefs free tool |
| `[further_reading][/further_reading]` | Related articles list | End of article, 2–4 related posts |

---

## Syntax

### intro_text

```
[intro_text]First paragraph of the article that hooks the reader.[/intro_text]
```

### post_nav_link

```
[post_nav_link link_text="Section Title" section="section-slug"]

## Section Title

[/post_nav_link]
```

Section slug rules: lowercase, hyphens for spaces, no special characters.
"What is YouTube SEO?" → `section="what-is-youtube-seo"`

### recommendation

```
[recommendation title="Tip"]

Your tip content here. Can include paragraphs, lists, and images.

![](https://example.com/image.jpg)

[/recommendation]
```

Common titles: "Tip", "Pro tip", "Don't sleep on...", "Important", "Note".

### sidenote

```
[sidenote]

Additional context that's useful but not essential to the main point.

[/sidenote]
```

### editor_note

```
[editor_note editor="Joshua Hardwick" editor_photo="https://ahrefs.com/blog/wp-content/uploads/2017/09/me.jpg" editor_job="Head of Content"]

Editor's commentary or update notice.

[/editor_note]
```

### blockquote

```
[blockquote size="small" author="John Mueller" author_photo="https://ahrefs.com/blog/wp-content/uploads/2022/02/john-mueller-google.png" author_job="Search Advocate," link_text="Google" link_url="https://www.google.com"]

_The quoted text goes here, typically in italics._

[/blockquote]
```

Known author photos:
- John Mueller — `https://ahrefs.com/blog/wp-content/uploads/2022/02/john-mueller-google.png`
- Ryan Law — `https://ahrefs.com/blog/wp-content/themes/Ahrefs-4/images/authors/main/RyanLaw.jpg`

### caption

```
[caption id="attachment_000000" align="alignnone" width="1365"]![Alt text](https://ahrefs.com/blog/wp-content/uploads/YYYY/MM/image.png) Caption text describing the image.[/caption]
```

Use placeholder id `attachment_000000` — the CMS assigns the real one on upload.

### toolWidget

```
[toolWidget tool="Keyword Generator" heading="Find thousands of keyword ideas in seconds"]
```

Available tools and their standard headings:

| tool | heading |
|---|---|
| `Website Traffic Checker` | See search traffic estimates for any website or webpage |
| `Website Authority Checker` | Check the authority of your domain |
| `Backlink Checker` | Get a glimpse into the power of our premium tool |
| `Keyword Generator` | Find thousands of keyword ideas in seconds |
| `Keyword Difficulty Checker` | See how hard it will be to get into top 10 search results |

### further_reading

```
[further_reading]

- [Article Title 1](https://ahrefs.com/blog/slug-1/)
- [Article Title 2](https://ahrefs.com/blog/slug-2/)
- [Article Title 3](https://ahrefs.com/blog/slug-3/)

[/further_reading]
```

Pick 2–4 genuinely related Ahrefs blog posts.

---

## Transformation workflow

### 1. Read and identify

Scan the draft for: the intro paragraph, every H2, tips/recommendations, expert quotes, image placeholders, and Ahrefs free-tool mentions.

### 2. Apply shortcodes

**Intro** — wrap the first paragraph, then add the TOC before the first H2:

```
# Title

[intro_text]First paragraph...[/intro_text]

Rest of intro...

[intro_toc]
```

**Every H2** — wrap in `post_nav_link` with a slugified section value.

**Tips** — look for "Pro tip:" / "Tip:" prefixes, or callout-worthy standalone advice, and convert to `[recommendation title="Tip"]`.

**Expert quotes** — a markdown blockquote with an attribution line becomes `[blockquote]` with the author attributes filled in.

**Images** — `[SCREENSHOT: description]` placeholders become `[caption]` blocks with `IMAGE_URL_PLACEHOLDER` until the real asset is uploaded. Every image needs alt text.

**Further reading** — add before the CTA at the end.

### 3. Clean up

1. Remove the metadata header (Target Keyword, Word Count, Status, Style Card).
2. Remove the Draft Notes section at the end.
3. Remove HTML comments.
4. Ensure a blank line before and after every shortcode.

### 4. Export

```bash
pandoc input.md -o output.docx --from markdown --to docx
```

If pandoc isn't installed, save the `.md` and note that manual conversion is needed.

---

## Worked example

**Before:**

```markdown
# YouTube SEO: How to Rank Your Videos in 2026

**Target Keyword**: youtube seo
**Status**: Sources Added

---

YouTube processes over 3 billion searches per month. That makes it the second-largest search engine in the world.

But here's the problem: over 500 hours of video get uploaded every minute.

## What is YouTube SEO?

YouTube SEO is the practice of optimizing your videos...

For a broader view of keyword opportunities, you can use Ahrefs' Keywords Explorer to check search volumes.

[SCREENSHOT: YouTube autocomplete suggestions]

---

## Draft Notes
...
```

**After:**

```
# YouTube SEO: How to Rank Your Videos in 2026

[intro_text]YouTube processes over 3 billion searches per month. That makes it the second-largest search engine in the world.[/intro_text]

But here's the problem: over 500 hours of video get uploaded every minute.

[intro_toc]

[post_nav_link link_text="What is YouTube SEO?" section="what-is-youtube-seo"]

## What is YouTube SEO?

[/post_nav_link]

YouTube SEO is the practice of optimizing your videos...

[recommendation title="Tip"]

For a broader view of keyword opportunities, you can use Ahrefs' Keywords Explorer to check search volumes and see related video keywords.

[/recommendation]

[caption id="attachment_000000" align="alignnone" width="1365"]![YouTube autocomplete suggestions](IMAGE_URL_PLACEHOLDER) YouTube's search autocomplete showing keyword suggestions.[/caption]
```

---

## Pushing to WordPress as a draft

If you have a WordPress API integration available, create the post with `status=draft`.
Quirks worth knowing on WordPress REST setups of this shape:

- Media deletion usually needs the media id plus `force=true`.
- `status` filters often expect a list (`["draft"]`), not a string.
- Some endpoints return incomplete metadata, so category ids may not be resolvable
  programmatically — create the post without a category and set it in wp-admin.
- Very long posts can return a truncated response with no id even though the post
  was created. Confirm by listing posts and matching on slug.
- WordPress may re-encode uploaded images (`.png` → `.jpg`); read the returned
  source URL rather than assuming the filename.

**Default to `status=draft`.** Never publish unless explicitly told to.
