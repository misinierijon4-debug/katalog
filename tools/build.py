"""Inject katalog.json into index_template.html -> index.html (single file + /images)."""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = r"C:\Users\Mirsad.Karasalihovic\Desktop\Mustertafeln-Katalog"

with open(os.path.join(HERE, "katalog.json"), encoding="utf-8") as f:
    data = json.load(f)
covers_path = os.path.join(HERE, "covers.json")
covers = {}
if os.path.exists(covers_path):
    with open(covers_path, encoding="utf-8") as f:
        covers = json.load(f)  # slug -> serie name

def slug(s):
    s = (s or "").lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

entries = []
for e in data["entries"]:
    has_img = os.path.exists(os.path.join(PROJ, "images", "thumb", e["id"] + ".jpg"))
    sl = slug(e.get("serie"))
    out = {
        "id": e["id"], "seite": e["seite"], "serie": e["serie"], "name": e.get("name"),
        "material": e["material"], "codes": e["codes"],
        "tafel_groesse": e["tafel_groesse"], "gt": e["gt"],
        "artikel": [{k: v for k, v in a.items() if v is not None} for a in e["artikel"]],
        "label": e["label"], "notizen": e["notizen"],
        "display": e["display"], "img": has_img,
    }
    if sl in covers:
        out["_covkey"] = sl
    if e.get("unklar"):
        out["unklar"] = e["unklar"]
    entries.append(out)

with open(os.path.join(PROJ, "index_template.html"), encoding="utf-8") as f:
    html = f.read()

html = html.replace("/*__DATA__*/[]", json.dumps(entries, ensure_ascii=False, separators=(",", ":")))
html = html.replace("/*__COVERS__*/{}", json.dumps(covers, ensure_ascii=False, separators=(",", ":")))

with open(os.path.join(PROJ, "index.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("built index.html with", len(entries), "entries,", sum(1 for e in entries if e["img"]), "with images")
