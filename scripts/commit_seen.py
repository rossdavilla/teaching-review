#!/usr/bin/env python3
"""Mark a month's candidate DOIs as seen, so later runs don't re-report them
(articles reappear when an online-first paper is later assigned to an issue)."""
import json, os, sys, glob
from datetime import datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
stamp = sys.argv[1] if len(sys.argv) > 1 else None
if not stamp:
    cands = sorted(glob.glob(os.path.join(ROOT, "data", "candidates_[0-9]*-[0-9]*.json")))
    cands = [c for c in cands if "_PSY" not in c]
    if not cands: sys.exit("no candidates_YYYY-MM.json found")
    stamp = os.path.basename(cands[-1])[11:18]
p = os.path.join(ROOT, "data", f"candidates_{stamp}.json")
d = json.load(open(p))
sp = os.path.join(ROOT, "data", "seen_dois.json")
cur = json.load(open(sp)) if os.path.exists(sp) else {"dois": [], "log": []}
before = set(cur["dois"])
new = [a["doi"] for a in d["articles"] if a["doi"] not in before]
cur["dois"] = sorted(before | set(new))
cur["log"].append({"stamp": stamp, "added": len(new), "at": datetime.now().isoformat(timespec="seconds")})
json.dump(cur, open(sp, "w"), indent=2)
print(f"{stamp}: +{len(new)} DOIs marked seen ({len(cur['dois'])} total)")
