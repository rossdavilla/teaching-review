# Journal Scraper

A monthly review of new psychology research, mapped to the lectures of three courses.

Scans 21 top-tier journals, pulls new articles with abstracts, and produces a report saying which lecture
each relevant finding belongs in — and which existing slides a new finding should change.

## Use it

```bash
python3 -I scripts/fetch_articles.py
```

That writes `data/candidates_YYYY-MM.json` plus one file per course. Then ask Claude in this directory to
"write this month's teaching review"; it produces `reports/YYYY-MM.md`. Accept it and run:

```bash
python3 -I scripts/commit_seen.py
```

so the same articles don't come back next month.

## What's here

```
config/journals.json          21 journals with ISSNs, course tags, abstract-source notes
scripts/extract_lectures.py   lecture PDFs -> data/lecture_text/ (run only when decks change)
scripts/fetch_articles.py     Crossref -> Europe PMC -> OpenAlex cascade, dedupe, junk filter
scripts/commit_seen.py        mark a month's DOIs as reported
data/lecture_index.json       37 lectures: topics, theories, researchers, key claims, keywords
data/seen_dois.json           dedupe ledger
reports/YYYY-MM.md            the monthly review
```

`CLAUDE.md` holds the review playbook and the design reasoning.

## Why it's built this way

Discovery is free and complete through open scholarly APIs; **abstracts** are the hard part and depend
entirely on the publisher. Measured over a 5-month window, Crossref carried abstracts for Wiley and SAGE
titles but none for APA or Springer; Europe PMC covered those but missed the non-biomedical ones; Elsevier
deposits abstracts essentially nowhere. Cascading all three gets ~82% coverage across these 21 journals,
and every item carries a real DOI — so a fabricated citation is structurally impossible.

Articles are tracked by when they were *indexed*, not their issue date, because these journals publish
online-first months ahead of issue assignment.
