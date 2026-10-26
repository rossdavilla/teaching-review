# Teaching Review

A monthly review of new psychology research, mapped to the lectures of three courses.

**Live:** https://rossdavilla.github.io/teaching-review/

> **Lecture materials are deliberately not in this repo.** The course PDFs and the text extracted
> from them are gitignored: they are course content, and the extracts contain named student
> responses recorded in class. Clone this and the scripts run, but `scripts/extract_lectures.py`
> and the review step need those local folders.

Scans 21 top-tier journals, pulls new articles with abstracts, and produces a report saying which lecture
each relevant finding belongs in — and which existing slides a new finding should change.

## Once a month, three steps

**1. Scan for new articles.** In Terminal:

```bash
cd ~/GitHub/Journal\ Scraper && ./start-month.sh
```

Takes a few minutes. It asks 21 journals what they published in the last 31 days, skips anything
already reported, and fetches abstracts.

**2. Ask Claude for the review.** Open this folder in Claude Code and say:

> write this month's teaching review

Claude reads the new articles against your lecture index, sorts them into Priority / Updates /
Examples / Retractions, and writes the slide text. Read it, push back, ask for changes.

**3. Publish.** When you're happy with it:

```bash
./finish-month.sh
```

Builds the report and the web page, marks the month as seen so it never reappears, and pushes.
The public page updates by itself a minute later. If you also want the private Claude version
refreshed, say "publish the artifact" in that session.

That's the whole routine. Steps 1 and 3 are one command each; the thinking happens in step 2.

## What's here

```
start-month.sh                step 1 — scan the journals
finish-month.sh               step 3 — build, mark seen, push
config/journals.json          21 journals with ISSNs, course tags, abstract-source notes
scripts/extract_lectures.py   lecture PDFs -> data/lecture_text/ (run only when decks change)
scripts/fetch_articles.py     Crossref -> Europe PMC -> OpenAlex cascade, dedupe, junk filter
scripts/commit_seen.py        mark a month's DOIs as reported
data/lecture_index.json       37 lectures: topics, theories, researchers, key claims, keywords
data/seen_dois.json           dedupe ledger
reports/YYYY-MM.md            the monthly review
```

`scripts/build_site.py` writes the page to **both** `site/index.html` (the Claude artifact publishes
from this path, so it must not move) and `docs/index.html` (what GitHub Pages serves). Push to `main`
and the public page redeploys.

`CLAUDE.md` holds the review playbook and the design reasoning.

## Why it's built this way

Discovery is free and complete through open scholarly APIs; **abstracts** are the hard part and depend
entirely on the publisher. Measured over a 5-month window, Crossref carried abstracts for Wiley and SAGE
titles but none for APA or Springer; Europe PMC covered those but missed the non-biomedical ones; Elsevier
deposits abstracts essentially nowhere. Cascading all three gets ~82% coverage across these 21 journals,
and every item carries a real DOI — so a fabricated citation is structurally impossible.

Articles are tracked by when they were *indexed*, not their issue date, because these journals publish
online-first months ahead of issue assignment.
