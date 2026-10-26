#!/usr/bin/env python3
"""Generate site/index.html from the curation + refs + candidates files.

Every month with a data/curation_YYYY-MM.json is embedded, newest first, so the page is
self-contained and complete on first paint (no fetch).

Usage: python3 -I scripts/build_site.py
"""
import glob, json, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATS = [("priority", "Priority"), ("updates", "Updates"),
        ("examples", "Examples"), ("retractions", "Retractions")]

# Proper nouns to keep capitalized when sentence-casing a title for a filename.
PROPER = {"indigenous", "christian", "muslim", "german", "germany", "swedish", "spanish",
          "australian", "asian", "american", "british", "canadian", "japanese", "chinese",
          "nigerian", "slovak", "italian", "dutch", "polish", "czech", "serbian", "turkish",
          "covid", "cupid", "europe", "harvard", "netherlands",
          "january", "february", "march", "april", "may", "june", "july", "august",
          "september", "october", "november", "december"}
STOP = {"a", "an", "the", "of", "in", "on", "to", "for", "and", "or", "with", "from",
        "into", "at", "by", "as", "is", "are", "its"}
# Proper-noun phrases keep their case: journal names quoted inside an article title,
# named phenomena, and multi-word place names whose parts are ambiguous on their own.
PHRASES = ["Journal of Applied Psychology", "Personnel Psychology", "Queen Bee",
           "South Asian", "United States"]


def _norm_punct(t):
    """Normalize the dash and quote variants publishers use, so downstream regexes
    and the acronym test see plain ASCII forms."""
    for a, b in [("‐", "-"), ("‑", "-"), ("‒", "-"), ("–", "-"),
                 ("—", "-"), ("−", "-"), ("‘", "'"), ("’", "'"),
                 ("“", '"'), ("”", '"')]:
        t = t.replace(a, b)
    return re.sub(r"\(\s+([^)]*?)\s+\)", r"(\1)", t)       # "( MOFS )" -> "(MOFS)"


def _depossess(w):
    return re.sub(r"'s?$", "", w)


def _cap_first_letter(w):
    """Capitalize the first alphabetic character, leaving any opening quote or bracket."""
    for i, ch in enumerate(w):
        if ch.isalpha():
            return w[:i] + ch.upper() + w[i + 1:]
    return w


def _case_word(w, first):
    """Sentence-case one word: keep acronyms, internal caps and proper nouns."""
    core = re.sub(r"[^A-Za-z0-9'/-]", "", w)
    if len(core) > 1 and re.sub(r"[-'/]", "", core).isupper():
        return w                                            # AI, LLM, UK, MOFS
    bare = _depossess(core).strip("-'/")
    if bare.lower() in PROPER:
        return _cap_first_letter(w)
    if re.search(r"[a-z][A-Z]", re.sub(r"[-/]", " ", core)):
        return w                                            # ChatGPT, McDeavitt
    if first:
        head = _cap_first_letter(w)
        for i, ch in enumerate(head):
            if ch.isalpha():
                return head[:i + 1] + head[i + 1:].lower()
        return head
    parts, out = re.split(r"([-/])", w), []
    for part in parts:
        if part in "-/":
            out.append(part); continue
        pc = re.sub(r"[^A-Za-z0-9]", "", part)
        out.append(part if (len(pc) > 1 and pc.isupper()) else part.lower())
    return "".join(out)


def _apply_phrases(t):
    marks = {}
    for i, ph in enumerate(PHRASES):
        if ph in t:
            key = f"\u0001{i}\u0001"
            marks[key] = ph
            t = t.replace(ph, key)
    return t, marks


def sentence_case_segments(t):
    """Sentence-case a title, restarting capitalization after . : ? !"""
    t, marks = _apply_phrases(t)
    out = []
    for seg in re.split(r"(?<=[:?!])\s+", t):
        words, seg_out = seg.split(), []
        for j, w in enumerate(words):
            seg_out.append(w if w.startswith("\u0001") else _case_word(w, j == 0))
        out.append(" ".join(seg_out))
    t = " ".join(out)
    for key, ph in marks.items():
        t = t.replace(key, ph)
    return t


def apa_title(title):
    """APA 7 sentence case for an article title."""
    return sentence_case_segments(_norm_punct(title).strip().rstrip("."))


def sentence_case(title):
    """Title text for a filename: drop a leading quoted phrase (publishers often open with
    a participant quote) and any subtitle, then sentence-case what remains."""
    t = _norm_punct(title).strip()
    t = re.sub(r'^"[^"]{0,160}"\s*[:,]\s*', "", t).strip()
    t = re.split(r"[:?!]", t)[0].strip().rstrip(".").strip('"')
    return sentence_case_segments(t)


def short_title(title, limit=50):
    t = re.sub(r"\s+", " ", sentence_case(title)).strip()
    if len(t) > limit:
        cut = t[:limit + 1]
        if " " in cut:
            cut = cut[:cut.rfind(" ")]
        t = cut
    words = t.split()
    while len(words) > 2 and words[-1].lower().strip(",;") in STOP:
        words.pop()
    return " ".join(words).strip().rstrip(",;-")


def safe_filename(s):
    s = _norm_punct(unicodedata.normalize("NFC", s)).replace('"', "")
    s = re.sub(r'[/\\:*?"<>|]', "", s)
    return re.sub(r"\s+", " ", s).strip().rstrip(".")


# ---------- APA 7 reference ----------

def _initials(given):
    out = []
    for part in re.split(r"[\s.]+", given or ""):
        part = "".join(ch for ch in part if ch.isalpha() or ch == "-").strip("-")
        if not part:
            continue
        if "-" in part:                       # hyphenated given name: J.-P.
            out.append("-".join(f"{p[0]}." for p in part.split("-") if p))
        else:
            out.append(f"{part[0]}.")
    return " ".join(out)


def apa_author_list(authors):
    names = [f"{a['family'].strip().strip(',')}, {_initials(a['given'])}".strip().rstrip(",")
             for a in authors]
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]}, & {names[1]}"
    if len(names) <= 20:
        return ", ".join(names[:-1]) + f", & {names[-1]}"
    return ", ".join(names[:19]) + ", ... " + names[-1]


def apa_reference(r, doi):
    bits = [apa_author_list(r["authors"])]
    bits.append(f"({r['year']}).") if r.get("year") else bits.append("(n.d.).")
    title = apa_title(r["title"])
    bits.append(title if title.endswith(("?", "!", ".")) else f"{title}.")
    journal = _norm_punct(r["journal"]).rstrip(". ")
    if r.get("volume"):
        loc = f"{journal}, {r['volume']}"
        if r.get("issue"):
            loc += f"({r['issue']})"
        pg = r.get("page") or r.get("article_number")
        loc += f", {pg}." if pg else "."
        bits.append(loc)
    else:
        bits.append(f"{journal}. Advance online publication.")
    bits.append(f"https://doi.org/{doi}")
    return " ".join(b for b in bits if b)


def cite_authors(authors):
    """APA in-text style: Smith / Smith & Jones / Smith et al."""
    fams = [a["family"].strip().strip(",") for a in authors]
    if not fams:
        return "Unknown"
    if len(fams) == 1:
        return fams[0]
    if len(fams) == 2:
        return f"{fams[0]} & {fams[1]}"
    return f"{fams[0]} et al"


def build_filename(r):
    return safe_filename(f"{cite_authors(r['authors'])} {r.get('year') or 'nd'} - {short_title(r['title'])}")


# ---------- assemble ----------

def load_months():
    months = []
    for cp in sorted(glob.glob(os.path.join(ROOT, "data", "curation_*.json")), reverse=True):
        cur = json.load(open(cp))
        stamp = cur["month"]
        refs = json.load(open(os.path.join(ROOT, "data", f"refs_{stamp}.json")))
        sp = os.path.join(ROOT, "data", f"slides_{stamp}.json")
        slides = json.load(open(sp)) if os.path.exists(sp) else {}
        items = []
        for it in cur["items"]:
            doi = it["doi"].lower()
            r = refs.get(doi)
            if not r:
                print(f"  !! no refs entry for {doi}"); continue
            items.append({
                "doi": doi, "cat": it["category"], "courses": it["courses"],
                "lectures": it["lectures"], "finding": it["finding"], "why": it["why"],
                "caution": it.get("caution"),
                "title": r["title"].rstrip(". "), "journal": r["journal"].rstrip(". "),
                "authorsShort": cite_authors(r["authors"]) + (
                    "." if cite_authors(r["authors"]).endswith("et al") else ""),
                "year": r.get("year"),
                "abstract": r.get("abstract") or "",
                "absSrc": r.get("abstract_source"),
                "apa": apa_reference(r, doi),
                "file": build_filename(r),
                "slide": slides.get(doi),
            })
        counts = {k: sum(1 for i in items if i["cat"] == k) for k, _ in CATS}
        months.append({"month": stamp, "label": cur["label"], "window": cur["window"],
                       "stats": cur["stats"], "counts": counts, "items": items})
    return months


TEMPLATE_HEAD = open(os.path.join(ROOT, "scripts", "site_template.html")).read()


def main():
    months = load_months()
    data = json.dumps(months, ensure_ascii=False).replace("<", "\\u003c")
    html = TEMPLATE_HEAD.replace("/*__DATA__*/", f"const MONTHS={data};")
    # site/ is what the Claude artifact publishes from (keeping that path keeps its URL);
    # docs/ is what GitHub Pages serves. Same bytes, written to both.
    for sub in ("site", "docs"):
        out = os.path.join(ROOT, sub, "index.html")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w").write(html)
    out = os.path.join(ROOT, "site", "index.html")
    tot = sum(len(m["items"]) for m in months)
    print(f"built site/index.html — {len(months)} month(s), {tot} items, {len(html)} bytes")
    for m in months:
        print(f"  {m['label']}: " + "  ".join(f"{lbl} {m['counts'][k]}" for k, lbl in CATS))
        ns = sum(1 for i in m["items"] if i.get("slide"))
        nc = sum(1 for i in m["items"] if (i.get("slide") or {}).get("current"))
        print(f"    slide text {ns}/{len(m['items'])} ({nc} with current wording)")

if __name__ == "__main__":
    main()
