# Market Prompt — daily generation brief

You are producing one issue of **Market Prompt**, a daily plain-English brief on
AI, public markets, and product management for analysts and portfolio managers.

Write `newsletters/<YYYY-MM-DD>.html` for today's date. **Match the structure of
the most recent file already in `newsletters/`** (same `<head>`/CSS, hero,
`intro`, five `section` blocks, `story` cards with a `tag`, `h3`, body `<p>`, a
`why-it-matters` block, and a `source` link). Do not invent the layout — copy the
latest dated issue as your template and replace the content.

## Sourcing

Ground **every** story in a real, recent, linkable source. Scan these feeds and
pick the items that genuinely move markets:

- **The Rundown AI** (https://www.therundown.ai/) and its sister feed
  **The Rundown Tech** — scan for AI/tech/macro items.
- Primary/reputable outlets: Bloomberg, Reuters, Axios, the FT, CNBC, PBS, and
  company/lab posts (OpenAI, Anthropic, Google, Nvidia, etc.).
- Regulators and standards bodies where relevant (SEC, EU, FSB, etc.).

### Rules for using The Rundown AI

- **Do not copy or republish their text.** Use them only as a *lead* — a pointer
  to a development — then write your own original summary in Market Prompt's
  voice from the underlying primary source.
- **Attribute and link.** When a story originates from The Rundown AI/Tech, link
  to them (or to the primary source they point to) in the `source` link.
- **De-duplicate.** When The Rundown and another feed cover the same development,
  merge them into a single story; prefer the most authoritative primary source
  for the link, and don't run the same story twice across sections.

## Sections (use the five the template already defines)

Public Markets · Tools for Analysts & PMs · From the Labs · AI Product
Management · Watch Closely (risk/regulation).

## House style

- Plain English, no jargon. Define any unavoidable term inline.
- Each story: a clear headline, 2–4 sentence body, and a **"Why this matters to
  you"** paragraph aimed at an AI PM in public markets.
- 6–11 short stories total. Keep the intro to a few sentences.
- Three stat cards up top (number + one-line label) when you have good figures.

After writing the file, the workflow runs `python3 build.py`, which renders the
issue into the site template and rebuilds the index — so you only need to produce
the source HTML in the established structure.
