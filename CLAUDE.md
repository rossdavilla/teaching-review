# Journal Scraper — monthly teaching review

Scans 21 top-tier psychology journals for new articles relevant to Ross's three courses, then maps the
findings to specific lectures and flags lecture content that should be updated.

## Courses

| Code | Course | Lectures present |
|---|---|---|
| PSY157 | Personal Relationships | 1–10, 13, 14 |
| PSY170 | Industrial/Organizational Psychology | 1–13 |
| PSY175 | Human Sexuality | 1–6, 8–12, 16 (7, 13–15 missing from the folder) |

## Monthly run

```bash
python3 -I scripts/fetch_articles.py              # last 31 days
```

Then start a session here and say **"write this month's teaching review."** Follow the playbook below.
That produces `data/curation_YYYY-MM.json` and `data/slides_YYYY-MM.json`, then:

```bash
python3 -I scripts/fetch_refs.py YYYY-MM          # structured authors/volume for APA references
python3 -I scripts/build_report.py YYYY-MM        # regenerates reports/YYYY-MM.md
python3 -I scripts/build_site.py                  # regenerates site/index.html with every month
python3 -I scripts/commit_seen.py                 # stop these articles reappearing next month
```

The page has two homes, both written by `build_site.py`:

- `site/index.html` — publish to the **Claude artifact** (private): https://claude.ai/artifact/JMBay7gB1Rpi7ZN45Yyij7
- `docs/index.html` — committed and pushed to **GitHub Pages** (public): https://rossdavilla.github.io/teaching-review/

Keep the `site/` path exactly as it is; the artifact's URL is tied to it, and moving the file would
create a second artifact. After a month is added, publish the artifact *and* `git push`.

**Never commit the lecture folders or `data/lecture_text/`** — see `.gitignore`. The extracted text
contains named student responses recorded in class, and the repo is public.

### The three files a review produces

| File | Holds |
|---|---|
| `data/curation_YYYY-MM.json` | category, courses, lectures, finding, why, caution — plus the month `narrative` (intro, cross-course items, coverage notes, lecture gaps, and the Retractions-empty explanation) |
| `data/slides_YYYY-MM.json` | per DOI: `current` slide wording (quoted from the deck) and `proposed` slide |

**Write those two files; never hand-write the outputs.** `reports/YYYY-MM.md` and `site/index.html` are both
*generated* from them plus `data/refs_*.json` and `data/candidates_*.json`, so the report and the page cannot
drift apart. `build_site.py` owns APA reference formatting and the download filenames; `build_report.py`
imports them so both surfaces agree. Editing a generated file by hand gets overwritten on the next build.

The report's "Slides to update" table is derived automatically from every item whose `slide` entry has a
`current` block — so adding current wording to an item is what puts it in that table.

### Card actions on the site

Each card offers **Abstract**, **Slide text**, **Copy APA reference** and **Continue in Claude**, plus a
checkbox that feeds the download-instructions builder.

**Continue in Claude** copies a full briefing — article, abstract, course and lecture, the finding, why it
matters, current slide wording, proposed replacement, and any caveat — ending with an instruction to reply
only "Ready" and wait. Ross pastes it as the first message of a fresh chat and asks follow-ups from there.

One thing to preserve if you touch that code: the curation prose is written **to** Ross ("your slides"),
but in that prompt Ross is the speaker, so `toFirstPerson()` flips every you/your to I/my. Keep the review
text in second person — the flip happens only in the Claude prompt, not on the cards or in the report.

Re-run `scripts/extract_lectures.py` and rebuild `data/lecture_index.json` only when the lecture decks change.

## The review playbook

1. Read `data/lecture_index.json` (37 lectures: topics, theories, researchers, `key_claims`, `match_keywords`).
   This is the matching asset — `key_claims` are the teachable assertions new work can update or contradict.
2. Read `data/candidates_YYYY-MM_<COURSE>.json` for each course. Abstracts are stored in full.
3. For each course, select items that either **conflict with / update a `key_claim`** or **make a better
   classroom example than what is on the slide now**. That is the agreed flagging level — not everything
   topically adjacent.
   **Calibration:** October 2026 flagged 58 of 165 articles (~35%). Ross reviewed that volume and confirmed
   it was right, so aim for the same density rather than trimming or expanding it.

### The four categories

Every flagged article goes in **exactly one** category. Many fit two; pick the most useful one and move on —
the point is short, scannable lists.

| Category | What belongs in it |
|---|---|
| **Priority** | The reads worth his time first, whatever the reason. Roughly 5–6 per course. |
| **Updates** | Changes, sharpens or complicates a claim already on a slide. |
| **Examples** | Better classroom material where nothing currently taught is wrong. |
| **Retractions** | New work means a claim should come **off** a slide — a serious replication failure, or a reversal of an accepted effect. |

**Retractions is deliberately strict.** A single null result does not qualify. October 2026 had none, and an
empty Retractions tab is the expected outcome in most months — say so rather than promoting a weak candidate
to fill it.

There is no "read with care" category. Caveats (small N, no abstract, contested literature) go in the
per-item `caution` field instead, which renders as a note on the card.
4. Write `reports/YYYY-MM.md`. For each priority item give: journal, authors, DOI link, the lecture it maps to,
   the finding with its actual numbers, and a **"Why it matters for you"** line that names the specific slide
   content it touches.
5. End each course section with a **"Lecture material to update"** table: current slide content → suggested change.
6. Close with cross-course items and coverage notes.

### Writing slide text

Every item gets a `slide` entry. `proposed` is a slide title plus 4–7 short bullets — write them as spoken
lines, not prose. Include `current` **only** when the article bears on a slide that already exists: quote the
real wording from `data/lecture_text/<COURSE>-<NN>.txt` rather than paraphrasing it, so he can see exactly
what changes. 29 of October's 58 had a current slide.

Note that PSY175 decks are fill-in-the-blank: the handout export often shows a heading and little else,
because words are revealed in class. Quote what is there and say so rather than inventing the missing text.

### Rules that matter

- **Never cite a DOI that is not in the candidates file.** Verify before finishing:
  every `https://doi.org/...` in the report must appear in `data/candidates_YYYY-MM.json`.
- **Read the full abstract before summarizing a result.** Truncated abstracts have reversed conclusions here
  before — the SDT necessity paper *confirmed* the necessity claim; a 850-character preview implied it refuted it.
- **Mark small or weak studies** with ⚠️ and the reason (N = 88 convenience sample, single site, etc.).
- **Flag contested literatures** rather than silently recommending or omitting them. Say why it is contested
  and let Ross decide the framing. Offer a counterweight from the same window where one exists.
- **Say when an abstract was unavailable.** Do not infer content from a title.
- Note lecture *gaps* found while matching (topics with no slide coverage), separately from journal findings.

## Journal list

`config/journals.json` — 21 journals, each tagged with the courses it serves. Abstract availability was
verified empirically and is publisher-dependent:

- **Wiley / SAGE** → Crossref carries abstracts (JSPR, Personal Relationships, Personnel Psychology, JOB, PSPB, Perspectives)
- **Springer / Taylor & Francis / APA** → Crossref has none; Europe PMC does (Archives of Sexual Behavior, JSR, JSMT, JAP, JPSP, J Family Psych, Psych Review)
- **Elsevier** → neither; OpenAlex partially (Leadership Quarterly, J Vocational Behavior, Current Opinion)
- **Nature Reviews Psychology** → no abstracts in any open source; title and authors only

The fetcher cascades Crossref → Europe PMC → OpenAlex automatically, so adding a journal needs only its ISSN.
Verify a new ISSN resolves before trusting a zero-result run — a wrong ISSN returns nothing silently.

## Design notes

- Discovery uses Crossref **`from-created-date`**, not publication date: these journals publish online-first
  months before an article is assigned to an issue, so issue-based tracking would surface findings a year late.
- `data/seen_dois.json` is what prevents an online-first article being re-reported when it later lands in an issue.
- Slide-level positions are deliberately **not** in the lecture index. The handout PDFs interleave three slides
  per page with trailing slide numbers, so slide numbers cannot be recovered reliably. Match on
  theory / researcher / claim instead.
- No vector database or embeddings. The whole lecture corpus is ~35K tokens and fits in context; embedding
  similarity would also miss conceptual matches (e.g. a pay-transparency finding belonging in the Motivation
  lecture because that deck teaches equity theory).
- `scripts/extract_lectures.py` skips the `N 0Title.pdf` files — they are 1-page title cards, not content —
  and the combined `Lectures - All.pdf` decks.

## Environment gotcha

This machine's Python 3.14 framework build has no root certificates, so `urllib` TLS verification fails.
`scripts/fetch_articles.py` falls back to `curl` automatically. To fix it properly:
`/Applications/Python\ 3.14/Install\ Certificates.command`
