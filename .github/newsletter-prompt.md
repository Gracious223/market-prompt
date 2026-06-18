# Market Prompt — daily generation brief

You are producing one issue of **Market Prompt**, a daily plain-English brief for
busy executives and curious beginners. Write `newsletters/<YYYY-MM-DD>.html` for
today's date, matching the structure of the most recent file already in
`newsletters/` (same `<head>`/CSS, hero, `intro`, five `section` blocks, `story`
cards with a `tag`, `h3`, body `<p>`, a `why-it-matters` block, and a `source`
link). Copy the latest dated issue as your template and replace the content.

## 1. What to cover — relevance bar (most important first)

Lead with the stories that matter most to **AI in public markets**, then AI +
finance more broadly. For every candidate story, ask: *"Does this change how a
public-market investor, analyst, or AI product manager should think or act?"* If
not, drop it. Prioritise, in order:

1. **AI in public markets** — AI-company IPOs and earnings (OpenAI, Anthropic,
   Nvidia, Microsoft, Google), AI-driven moves in stocks/indices, valuations,
   chip/infrastructure supply, AI's effect on specific sectors (software, banks).
2. **AI + finance** — AI in trading, research, risk, banking, regulation (SEC,
   EU AI Act, FSB), and money flowing into AI (funding, capex).
3. **Frontier AI that will hit markets next** — major model releases and
   capabilities, but only with a clear "why this matters to markets" angle.

Skip generic consumer-gadget or hobbyist AI news with no market relevance.

## 2. Who you're writing for — assume zero background

Write so someone who knows **nothing about AI and nothing about finance** can
follow every sentence. This is the most important rule.

- **Explain every term the first time it appears**, in a short parenthetical in
  plain words. Examples: "an IPO (the first time a company sells its shares to
  the public)", "tokens (the small chunks of text an AI is billed by)", "a
  buyback (when a company uses spare cash to buy its own shares, which usually
  nudges the price up)", "market cap (the total value of all a company's
  shares)".
- No unexplained jargon, acronyms, or insider shorthand. If you must use a term,
  define it.
- Short sentences. Concrete words over abstract ones. Active voice.
- Use a real, recent, linkable source for every story; attribute and link it.

## 3. Sourcing

Scan these and pick the few items that clear the relevance bar above:

- **MUST CHECK EVERY DAY — Anthropic Alignment Science Blog**
  (https://alignment.anthropic.com). Fetch this page on every run and read the
  latest posts. It publishes AI-safety / alignment research (interpretability,
  AI monitoring, jailbreak defenses, deceptive-AI detection). Capture anything
  new or relevant and translate it into plain English with a clear market/risk
  angle — e.g. "what this means for whether AI systems can be trusted in
  regulated finance." These items usually belong in **From the Labs** or
  **Watch Closely**. If there are no genuinely new posts since yesterday, say so
  and move on (don't manufacture a story). Link to the specific post.
- **The Rundown AI** (https://www.therundown.ai/) and **The Rundown Tech** — as
  *leads* only. Do **not** copy or republish their wording; follow them to the
  primary source and write your own original, beginner-friendly summary. Link to
  them or the primary source, and **de-duplicate** when feeds overlap (one story,
  best primary source).
- Primary/reputable outlets: Bloomberg, Reuters, the FT, CNBC, Axios, PBS, and
  company/lab/regulator posts.

## 4. Format & length — built for executive skimming

- **6–8 stories total** (quality over volume). Use the five sections the
  template defines: Public Markets · Tools for Analysts & PMs · From the Labs ·
  AI Product Management · Watch Closely.
- Each story: a clear headline; a **2–3 sentence** body (short!); and a **"Why
  this matters to you"** line of 1–2 sentences in plain English.
- The card preview is built automatically from your `intro`, so write the intro
  as **2–3 very short, punchy sentences** — each one a single, scannable idea an
  executive can read in seconds.
- Three stat cards up top (a number + a one-line plain-English label) when you
  have solid figures.

After you write the file, the workflow runs `python3 build.py`, which renders it
into the site template and rebuilds the index — so you only produce the source
HTML in the established structure.
