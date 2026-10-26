# Teaching Review

A monthly review of new psychology research, mapped to the lectures of three courses.

**Live:** https://rossdavilla.github.io/teaching-review/

> **Lecture materials are deliberately not in this repo.** The course PDFs and the text extracted
> from them are gitignored: they are course content, and the extracts contain named student
> responses recorded in class. Clone this and the scripts run, but `scripts/extract_lectures.py`
> and the review step need those local folders.

Scans 21 top-tier journals, pulls new articles with abstracts, and produces a report saying which lecture
each relevant finding belongs in — and which existing slides a new finding should change.

## Once a month

**The easy way — just ask.** Open this folder in Claude Code and say:

> do this month's journal review

Claude runs the scan, reads the new articles against your lectures, shows you what it found,
makes any changes you want, then publishes everything. You don't run anything yourself.

**The backup way — double-click.** If you'd rather not open a session, this folder has two files
you can double-click in Finder:

| Double-click | When | What happens |
|---|---|---|
| **1 Scan for new articles** | Start of the month | A black window opens and shows progress for a few minutes, then tells you what to do next |
| **2 Publish the review** | After Claude has written the review | Builds the report and the web page and puts them online |

Between those two you still need to ask Claude for the review itself — that's the part that
reads the articles and decides what matters for your lectures.

Either way the public page updates about a minute after step 2:
https://rossdavilla.github.io/teaching-review/

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
