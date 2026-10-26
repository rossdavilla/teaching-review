#!/usr/bin/env python3
"""Fetch full Crossref metadata (structured authors, volume, issue, pages) for the DOIs
a month's curation cites, so APA references can be built correctly rather than parsed
out of collapsed "Given Family" strings.

Usage: python3 -I scripts/fetch_refs.py 2026-10
"""
import json, os, re, subprocess, sys, time, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Crossref and OpenAlex ask for a contact address to grant the polite rate limits.
# Set CROSSREF_MAILTO in the environment (or a local .env); the calls work without it.
MAILTO = os.environ.get("CROSSREF_MAILTO", "")
UA = f"journal-scraper/1.0 (mailto:{MAILTO})" if MAILTO else "journal-scraper/1.0"


def get(url, tries=3):
    for n in range(tries):
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except Exception:
            p = subprocess.run(["curl", "-sL", "--max-time", "40", "-A", UA, url],
                               capture_output=True, text=True)
            if p.stdout.strip():
                try:
                    return json.loads(p.stdout)
                except Exception:
                    pass
        time.sleep(1.2 * (n + 1))
    return None


def strip_tags(s):
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    for a, b in [("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'),
                 ("&#39;", "'"), ("&apos;", "'")]:
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def main():
    stamp = sys.argv[1] if len(sys.argv) > 1 else "2026-10"
    cur = json.load(open(os.path.join(ROOT, "data", f"curation_{stamp}.json")))
    cands = {a["doi"].lower(): a
             for a in json.load(open(os.path.join(ROOT, "data", f"candidates_{stamp}.json")))["articles"]}

    refs, missing = {}, []
    for i, item in enumerate(cur["items"], 1):
        doi = item["doi"].lower()
        d = get(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}?mailto={MAILTO}")
        m = (d or {}).get("message") if (d or {}).get("status") == "ok" else None
        if not m:
            missing.append(doi); print(f"  !! {doi}"); continue
        authors = [{"given": a.get("given", ""), "family": a.get("family", "")}
                   for a in (m.get("author") or []) if a.get("family")]
        pub = (m.get("published") or m.get("issued") or {}).get("date-parts", [[None]])[0]
        src = cands.get(doi, {})
        refs[doi] = {
            "title": strip_tags((m.get("title") or [""])[0]),
            "journal": strip_tags((m.get("container-title") or [src.get("journal", "")])[0]),
            "authors": authors,
            "year": pub[0] if pub and pub[0] else None,
            "volume": m.get("volume"), "issue": m.get("issue"), "page": m.get("page"),
            "article_number": m.get("article-number"),
            "abstract": src.get("abstract", ""),
            "abstract_source": src.get("abstract_source"),
            "published": src.get("published"),
        }
        if i % 10 == 0:
            print(f"    ...{i}/{len(cur['items'])}")
        time.sleep(0.25)

    p = os.path.join(ROOT, "data", f"refs_{stamp}.json")
    json.dump(refs, open(p, "w"), indent=1)
    nauth = sum(len(r["authors"]) for r in refs.values())
    print(f"\n{len(refs)} refs, {nauth} structured authors -> {os.path.basename(p)}")
    if missing:
        print("missing:", missing)
    noauth = [d for d, r in refs.items() if not r["authors"]]
    nopage = [d for d, r in refs.items() if not r["page"] and not r["article_number"]]
    print(f"no authors: {len(noauth)} | no page/article number: {len(nopage)}")

if __name__ == "__main__":
    main()
