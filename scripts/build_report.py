#!/usr/bin/env python3
"""Generate reports/YYYY-MM.md from the same data the website is built from, so the
report and the page can never drift apart.

Sources: data/curation_YYYY-MM.json (categories + editorial prose + month narrative)
         data/refs_YYYY-MM.json     (structured authors, volume, pages)
         data/slides_YYYY-MM.json   (current vs proposed slide wording)
         data/candidates_YYYY-MM.json (abstracts, for the DOI verification pass)

Usage: python3 -I scripts/build_report.py [YYYY-MM]
"""
import glob, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_site import CATS, apa_reference, cite_authors  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COURSE = {"PSY157": "Personal Relationships",
          "PSY170": "Industrial/Organizational Psychology",
          "PSY175": "Human Sexuality"}
CATNOTE = {
 "priority": "The reads worth your time first — biggest consequence for what you teach.",
 "updates": "Findings that change, sharpen or complicate a claim already on a slide.",
 "examples": "Stronger classroom material than what the slide uses now, where nothing taught is wrong.",
 "retractions": "Findings that invalidate something you teach — a failed replication of an accepted "
                "effect, or a claim that should come off the slide."}
MONTH_NAME = {"01": "January", "02": "February", "03": "March", "04": "April", "05": "May",
              "06": "June", "07": "July", "08": "August", "09": "September", "10": "October",
              "11": "November", "12": "December"}


def anchor(text):
    return re.sub(r"[^a-z0-9\s-]", "", text.lower()).strip().replace(" ", "-")


def main():
    stamp = sys.argv[1] if len(sys.argv) > 1 else sorted(
        os.path.basename(p)[9:16] for p in glob.glob(os.path.join(ROOT, "data", "curation_*.json")))[-1]
    D = lambda n: json.load(open(os.path.join(ROOT, "data", f"{n}_{stamp}.json")))
    cur, refs, slides = D("curation"), D("refs"), D("slides")
    cands = {a["doi"].lower(): a for a in D("candidates")["articles"]}
    nar = cur.get("narrative", {})
    st = cur["stats"]
    yr, mo = stamp.split("-")

    items = []
    for it in cur["items"]:
        doi = it["doi"].lower()
        r = refs[doi]
        items.append({**it, "doi": doi, "r": r, "cat": it["category"],
                      "title": r["title"].rstrip(". "),
                      "journal": r["journal"].rstrip(". "),
                      "primary": it["courses"][0],
                      "others": it["courses"][1:]})

    L = []
    A = L.append
    A(f"# Teaching Review — {MONTH_NAME[mo]} {yr}")
    A("")
    A(f"**Window:** {cur['window']['since']} to {cur['window']['until']} · "
      f"**Journals scanned:** {st['journals']} · **New articles:** {st['new']}  ")
    pct = round(100 * st["abstracts"] / st["new"])
    A(f"**Abstracts retrieved:** {st['abstracts']}/{st['new']} ({pct}%) · "
      f"**Junk filtered:** {st['junk']} · **Flagged:** {st['flagged']}")
    A("")
    if nar.get("intro"):
        A(nar["intro"]); A("")
    counts = {k: sum(1 for i in items if i["cat"] == k) for k, _ in CATS}
    jump = " · ".join(f"[{lbl}](#{anchor(lbl)}--{counts[k]})" for k, lbl in CATS)
    A(f"**Jump to:** {jump}")
    A("")

    for key, lbl in CATS:
        A("---"); A("")
        A(f"## {lbl} — {counts[key]}")
        A("")
        A(f"*{CATNOTE[key]}*")
        A("")
        group = [i for i in items if i["cat"] == key]
        if not group:
            A(nar.get("retractions_none") if key == "retractions"
              else f"Nothing landed in this category this month.")
            A("")
            continue
        for code in ["PSY157", "PSY170", "PSY175"]:
            sub = [i for i in group if i["primary"] == code]
            if not sub:
                continue
            A(f"### {code} · {COURSE[code]} — {len(sub)}")
            A("")
            for it in sub:
                also = f" · also {', '.join(it['others'])}" if it["others"] else ""
                A(f"**{it['title']}**  ")
                cites = cite_authors(it["r"]["authors"])
                cites += "." if cites.endswith("et al") else ""
                A(f"*{it['journal']}* · {cites} · "
                  f"[{it['doi']}](https://doi.org/{it['doi']})  ")
                A(f"→ **{it['lectures']}**{also}")
                A("")
                A(it["finding"])
                A("")
                why = re.sub(r"</?b>", "**", it["why"])
                A(f"**Why it matters:** {why}")
                A("")
                if it.get("caution"):
                    A(f"> ⚠️ **Note.** {it['caution']}")
                    A("")

    # slide-change table, derived from every item whose article touches an existing slide
    A("---"); A("")
    A("## Slides to update")
    A("")
    A("Every article above that bears on wording already in a deck. The current column is quoted from the "
      "handout export, so a sparse entry means the slide is fill-in-the-blank and the words are revealed in class.")
    A("")
    for code in ["PSY157", "PSY170", "PSY175"]:
        rows = [(i, slides.get(i["doi"])) for i in items if i["primary"] == code]
        rows = [(i, s) for i, s in rows if s and s.get("current")]
        if not rows:
            continue
        A(f"### {code} · {COURSE[code]}")
        A("")
        A("| Lecture | Current slide | Proposed replacement |")
        A("|---|---|---|")
        for i, s in rows:
            A(f"| {i['lectures']} | **{s['current']['title']}** | **{s['proposed']['title']}** |")
        A("")

    if nar.get("cross_course"):
        A("---"); A("")
        A("## Cross-course items")
        A("")
        A("| Article | Serves |")
        A("|---|---|")
        for c in nar["cross_course"]:
            d = c["doi"].lower()
            A(f"| [{refs[d]['title'].rstrip('. ')}](https://doi.org/{d}) | {c['serves']} |")
        A("")

    A("---"); A("")
    A("## Coverage notes")
    A("")
    for n in nar.get("coverage", []):
        A(f"- {n}")
    if nar.get("gaps"):
        A("")
        A("**Lecture gaps noticed while matching** (not journal findings, but worth your attention):")
        A("")
        for g in nar["gaps"]:
            A(f"- {g}")
    A("")

    A("---"); A("")
    A("## Full references")
    A("")
    for it in sorted(items, key=lambda x: cite_authors(x["r"]["authors"]).lower()):
        A(f"- {apa_reference(it['r'], it['doi'])}")
    A("")

    out = os.path.join(ROOT, "reports", f"{stamp}.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    text = "\n".join(L)
    open(out, "w").write(text)

    cited = set(m.lower() for m in re.findall(r"https://doi\.org/([^\s)\]]+)", text))
    bad = [d for d in cited if d not in cands]
    print(f"built reports/{stamp}.md — {len(text)} bytes, {len(items)} items")
    print("  " + "  ".join(f"{lbl} {counts[k]}" for k, lbl in CATS))
    print(f"  DOIs cited: {len(cited)} | not in fetched data: {len(bad)}")
    if bad:
        print("  !!", bad)

if __name__ == "__main__":
    main()
