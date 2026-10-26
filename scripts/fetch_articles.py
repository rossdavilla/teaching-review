#!/usr/bin/env python3
"""Fetch newly-indexed articles from the configured journals, with abstracts.

Discovery is Crossref by ISSN (complete for the chosen journals). Abstracts cascade
Crossref -> Europe PMC -> OpenAlex, because abstract availability is publisher-dependent:
Wiley/SAGE deposit to Crossref; Springer/T&F/APA show up in Europe PMC; Elsevier in
neither (partial via OpenAlex). Every item carries a real DOI, so nothing downstream
can invent a citation.

Usage:
  python3 scripts/fetch_articles.py                 # last 31 days
  python3 scripts/fetch_articles.py --days 60
  python3 scripts/fetch_articles.py --since 2026-09-01 --until 2026-10-25
  python3 scripts/fetch_articles.py --no-dedupe     # ignore seen_dois.json
"""
import argparse, json, os, re, subprocess, sys, time, urllib.parse
from datetime import date, datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Crossref and OpenAlex ask for a contact address to grant the polite rate limits.
# Set CROSSREF_MAILTO in the environment (or a local .env); the calls work without it.
MAILTO = os.environ.get("CROSSREF_MAILTO", "")
UA = f"journal-scraper/1.0 (mailto:{MAILTO})" if MAILTO else "journal-scraper/1.0"

JUNK = re.compile(
    r"^(introduction|about the authors?|editorial board|erratum|correction|corrigendum|retraction"
    r"|index|front matter|back matter|acknowledg|table of contents|contents|issue information"
    r"|reviewer|thank you to|call for papers|in this issue|editor'?s? note|preface|foreword"
    r"|subject index|author index|copyright|masthead|supplemental material|supplementary material"
    r"|in memoriam|obituary|editorial overview|list of contributors|highlights from)", re.I)

# APA deposits supplements as their own DOIs ending in .supp; they are not articles.
JUNK_DOI = re.compile(r"\.supp$|/supp\b", re.I)


def _get(url, tries=3):
    """GET JSON. Prefers urllib; falls back to curl (macOS framework Python often
    ships without root certificates, which breaks urllib's TLS verification)."""
    for n in range(tries):
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except Exception:
            try:
                p = subprocess.run(["curl", "-sL", "--max-time", "40", "-A", UA, url],
                                   capture_output=True, text=True)
                if p.stdout.strip():
                    return json.loads(p.stdout)
            except Exception:
                pass
        time.sleep(1.5 * (n + 1))
    return None


def strip_tags(s):
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    s = (s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
          .replace("&quot;", '"').replace("&#39;", "'").replace("&apos;", "'"))
    s = re.sub(r"^\s*(abstract|summary)[:.\s]*", "", s, flags=re.I)
    return re.sub(r"\s+", " ", s).strip()


def from_inverted(idx):
    if not idx:
        return ""
    pos = [(p, w) for w, ps in idx.items() for p in ps]
    return " ".join(w for _, w in sorted(pos))


def crossref_journal(issn, since, until):
    out, cursor, seen_guard = [], "*", 0
    while True:
        url = ("https://api.crossref.org/journals/%s/works"
               "?filter=from-created-date:%s,until-created-date:%s,type:journal-article"
               "&rows=100&cursor=%s&mailto=%s"
               "&select=DOI,title,author,published,created,abstract,type,URL,container-title,"
               "volume,issue,page,is-referenced-by-count,subtitle") % (
            issn, since, until, urllib.parse.quote(cursor), MAILTO)
        d = _get(url)
        if not d or d.get("status") != "ok":
            break
        msg = d["message"]
        items = msg.get("items", [])
        out.extend(items)
        cursor = msg.get("next-cursor")
        seen_guard += 1
        if not cursor or not items or seen_guard > 12:
            break
        time.sleep(0.3)
    return out


def epmc_abstract(doi):
    q = urllib.parse.quote(f'DOI:"{doi}"')
    d = _get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={q}&format=json&pageSize=1&resultType=core")
    try:
        r = d["resultList"]["result"][0]
        return strip_tags(r.get("abstractText")), r.get("pmid")
    except Exception:
        return "", None


def openalex_abstract(doi):
    d = _get(f"https://api.openalex.org/works/https://doi.org/{urllib.parse.quote(doi)}?mailto={MAILTO}")
    try:
        return strip_tags(from_inverted(d.get("abstract_inverted_index"))), d.get("cited_by_count")
    except Exception:
        return "", None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=None)
    ap.add_argument("--since"); ap.add_argument("--until")
    ap.add_argument("--no-dedupe", action="store_true")
    ap.add_argument("--max-abstract-lookups", type=int, default=600)
    a = ap.parse_args()

    cfg = json.load(open(os.path.join(ROOT, "config", "journals.json")))
    days = a.days or cfg.get("window_days", 31)
    until = a.until or date.today().isoformat()
    since = a.since or (datetime.fromisoformat(until).date() - timedelta(days=days)).isoformat()

    seen_path = os.path.join(ROOT, "data", "seen_dois.json")
    seen = set()
    if os.path.exists(seen_path) and not a.no_dedupe:
        seen = set(json.load(open(seen_path)).get("dois", []))

    print(f"window {since} .. {until}   ({len(cfg['journals'])} journals, {len(seen)} DOIs already seen)\n")

    records, skipped_junk, dup = {}, 0, 0
    for j in cfg["journals"]:
        items = crossref_journal(j["issn"], since, until)
        kept = 0
        for it in items:
            doi = (it.get("DOI") or "").lower()
            title = strip_tags((it.get("title") or [""])[0])
            if not doi or not title:
                continue
            if JUNK.match(title) or len(title) < 15 or JUNK_DOI.search(doi):
                skipped_junk += 1; continue
            if doi in seen:
                dup += 1; continue
            if doi in records:
                continue
            auth = []
            for x in (it.get("author") or [])[:12]:
                nm = " ".join(p for p in [x.get("given"), x.get("family")] if p)
                if nm: auth.append(nm)
            pub = it.get("published", {}).get("date-parts", [[None]])[0]
            records[doi] = {
                "doi": doi, "title": title,
                "subtitle": strip_tags((it.get("subtitle") or [""])[0]) or None,
                "journal": j["name"], "issn": j["issn"], "courses": j["courses"],
                "publisher": j["publisher"], "authors": auth,
                "published": "-".join(str(p) for p in pub if p is not None),
                "created": (it.get("created", {}) or {}).get("date-time", "")[:10],
                "volume": it.get("volume"), "issue": it.get("issue"), "page": it.get("page"),
                "url": it.get("URL") or f"https://doi.org/{doi}",
                "cited_by": it.get("is-referenced-by-count"),
                "abstract": strip_tags(it.get("abstract")),
                "abstract_source": "crossref" if strip_tags(it.get("abstract")) else None,
            }
            kept += 1
        print(f"  {j['name'][:46]:48} crossref={len(items):>4}  new={kept:>4}")
        time.sleep(0.2)

    need = [r for r in records.values() if not r["abstract"]][: a.max_abstract_lookups]
    print(f"\n{len(records)} new articles | {len(records)-len(need)} abstracts from Crossref"
          f" | looking up {len(need)} via Europe PMC / OpenAlex")
    for i, r in enumerate(need, 1):
        ab, pmid = epmc_abstract(r["doi"])
        if ab:
            r["abstract"], r["abstract_source"], r["pmid"] = ab, "europepmc", pmid
        else:
            ab, cites = openalex_abstract(r["doi"])
            if ab:
                r["abstract"], r["abstract_source"] = ab, "openalex"
        if i % 25 == 0:
            print(f"    ...{i}/{len(need)}")
        time.sleep(0.12)

    recs = sorted(records.values(), key=lambda r: (r["journal"], r["title"]))
    have = sum(1 for r in recs if r["abstract"])
    stamp = until[:7]
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    allp = os.path.join(ROOT, "data", f"candidates_{stamp}.json")
    json.dump({"window": {"since": since, "until": until}, "generated": datetime.now().isoformat(timespec="seconds"),
               "counts": {"total": len(recs), "with_abstract": have, "junk_skipped": skipped_junk,
                          "already_seen": dup}, "articles": recs},
              open(allp, "w"), indent=2)

    for code in cfg["courses"]:
        sub = [r for r in recs if code in r["courses"]]
        p = os.path.join(ROOT, "data", f"candidates_{stamp}_{code}.json")
        json.dump({"course": code, "title": cfg["courses"][code]["title"],
                   "window": {"since": since, "until": until},
                   "count": len(sub), "articles": sub}, open(p, "w"), indent=2)
        ch = sum(len(r["abstract"]) for r in sub)
        print(f"  {code}: {len(sub):>4} articles, ~{ch//4:>6} tokens of abstract -> {os.path.basename(p)}")

    print(f"\nTOTAL {len(recs)} new | abstracts {have}/{len(recs)} ({100*have//max(len(recs),1)}%)"
          f" | junk filtered {skipped_junk} | already seen {dup}")
    print(f"-> {allp}")
    print("\nRun scripts/commit_seen.py after you accept a report to stop these re-appearing.")

if __name__ == "__main__":
    main()
