"""One-off: CAMPUS entries carried the poster article number (9336-CAM4-Y0 /
9336-CAM8-Y0) as a fourth tafel code with empty label. Move it to the label
("Poster 9336-…") in katalog.json AND katalog.js (manual_entries.py fixed
separately for future rebuilds)."""
import json, os, re

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def fix_entries(entries):
    n = 0
    for e in entries:
        codes = e.get("codes") or []
        poster = [c for c in codes if re.match(r"^93\d\d-", c)]
        if not poster:
            continue
        e["codes"] = [c for c in codes if c not in poster]
        if not e.get("label"):
            e["label"] = "Poster " + poster[0]
        n += 1
        print("  ", e["id"], "->", e["label"], "| codes:", e["codes"])
    return n

jpath = os.path.join(PROJ, "katalog.json")
with open(jpath, encoding="utf-8") as f:
    data = json.load(f)
ekey = next(k for k in data if "eintr" in k)
print("katalog.json:")
n1 = fix_entries(data[ekey])
with open(jpath, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)

jspath = os.path.join(PROJ, "katalog.js")
with open(jspath, encoding="utf-8") as f:
    src = f.read()
m = re.match(r"^window\.KATALOG_DATA = (.*);\s*$", src, re.S)
arr = json.loads(m.group(1))
print("katalog.js:")
n2 = fix_entries(arr)
with open(jspath, "w", encoding="utf-8") as f:
    f.write("window.KATALOG_DATA = " + json.dumps(arr, ensure_ascii=False, separators=(",", ":")) + ";\n")

print("gefixt:", n1, "in katalog.json,", n2, "in katalog.js")
