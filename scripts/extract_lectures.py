#!/usr/bin/env python3
"""Extract lecture text from course PDF decks into data/lecture_text/.

Skips combined "- All" decks and the 1-page title-card files (e.g. "3 0Male Sexual Anatomy.pdf"),
which carry no slide content. Normalizes the two different bullet templates in use.
"""
import json, os, re, sys, unicodedata
import fitz

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "lecture_text")
BULLETS = "•!¡¢§£•▪●‣⁃"

def clean(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    lines, out = text.split("\n"), []
    for ln in lines:
        s = ln.strip().lstrip(BULLETS).strip()
        if not s:
            continue
        if re.fullmatch(r"\d{1,3}", s):            # trailing slide numbers
            continue
        if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{2,4}", s):  # export date stamp
            continue
        if len(s) == 1:
            continue
        out.append(s)
    # collapse the duplicate-line artifact of handout exports
    dedup = [l for i, l in enumerate(out) if i == 0 or l != out[i - 1]]
    return "\n".join(dedup)

def lecture_files(folder: str):
    for fn in sorted(os.listdir(folder)):
        if not fn.lower().endswith(".pdf"):
            continue
        if re.search(r"-\s*All\.pdf$|\)\s*-\s*All\.pdf$", fn) or " - All" in fn or ") - All" in fn:
            continue
        if re.match(r"^\d+\s+0", fn):              # title-card file
            continue
        m = re.match(r"^(\d+)\s*[-\s]\s*(.+)\.pdf$", fn)
        num = int(m.group(1)) if m else None
        title = (m.group(2) if m else fn[:-4]).strip()
        yield fn, num, title

def main():
    cfg = json.load(open(os.path.join(ROOT, "config", "journals.json")))
    os.makedirs(OUT, exist_ok=True)
    manifest = []
    for code, meta in cfg["courses"].items():
        folder = os.path.join(ROOT, meta["folder"])
        if not os.path.isdir(folder):
            print(f"!! missing folder for {code}: {folder}", file=sys.stderr); continue
        for fn, num, title in lecture_files(folder):
            path = os.path.join(folder, fn)
            doc = fitz.open(path)
            raw = "\n".join(doc[i].get_text() for i in range(doc.page_count))
            txt = clean(raw)
            if len(txt) < 200:
                print(f"   skip (too short): {code} {fn}"); continue
            slug = f"{code}-{num:02d}" if num is not None else f"{code}-xx"
            with open(os.path.join(OUT, f"{slug}.txt"), "w") as fh:
                fh.write(f"# {code} Lecture {num}: {title}\n\n{txt}\n")
            manifest.append({"course": code, "lecture": num, "title": title,
                             "slug": slug, "pages": doc.page_count, "chars": len(txt)})
            print(f"   {slug}  {title[:44]:46} {doc.page_count:>2}p {len(txt):>6}ch")
    manifest.sort(key=lambda r: (r["course"], r["lecture"] if r["lecture"] is not None else 99))
    json.dump(manifest, open(os.path.join(ROOT, "data", "lecture_manifest.json"), "w"), indent=2)
    tot = sum(r["chars"] for r in manifest)
    print(f"\n{len(manifest)} lectures, {tot} chars (~{tot//4} tokens) -> data/lecture_text/")

if __name__ == "__main__":
    main()
