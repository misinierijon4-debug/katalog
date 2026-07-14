import copy
import json
import re
import shutil
from pathlib import Path

ROOT = Path(r"C:\Users\Mirsad.Karasalihovic\Desktop\Mustertafeln-Katalog")
BACKUP = Path(r"C:\Users\Mirsad.Karasalihovic\Desktop\Mustertafeln-Katalog_backup_2026-07-10")

def entries_of(data):
    key = next(k for k in data if "eintr" in k)
    return key, data[key]

current = json.loads((ROOT / "katalog.json").read_text(encoding="utf-8"))
backup = json.loads((BACKUP / "katalog.json").read_text(encoding="utf-8"))
key, entries = entries_of(current)
_, old_entries = entries_of(backup)
urban = [copy.deepcopy(e) for e in old_entries if e.get("serie") == "URBAN PULSE"]
urban_codes = {c for e in urban for c in e.get("codes", [])}

engers = [e for e in entries if e.get("marke") != "vb"]
vb_new = []
for entry in entries:
    if entry.get("marke") != "vb":
        continue
    if entry["id"].startswith("vb_"):
        entry["pdf_pfad"] = f"pages/vb/seite-{entry['seite']:03}.pdf"
        vb_new.append(entry)
        continue
    # Three old IDs were used as anchors for generic backing-board groups.
    generic_codes = [c for c in entry.get("codes", []) if c not in urban_codes]
    if generic_codes:
        entry = copy.deepcopy(entry)
        entry["codes"] = generic_codes
        primary = re.sub(r"[^A-Z0-9]", "", generic_codes[0].upper())
        entry["id"] = f"vb_p{entry['seite']:03}_{primary}"
        entry["pdf_pfad"] = f"pages/vb/seite-{entry['seite']:03}.pdf"
        vb_new.append(entry)

urban_dir = ROOT / "pages" / "vb" / "urban"
urban_dir.mkdir(parents=True, exist_ok=True)
for page_no in range(263, 282):
    shutil.copy2(BACKUP / "pages" / f"seite-{page_no:03}.pdf",
                 urban_dir / f"seite-{page_no:03}.pdf")

for entry in urban:
    entry["marke"] = "vb"
    entry["pdf_pfad"] = f"pages/vb/urban/seite-{entry['seite']:03}.pdf"

current[key] = engers + sorted(vb_new, key=lambda e: (e["seite"], e["id"])) + urban
current["probleme"] = [p for p in current.get("probleme", []) if "Bestehender V&B-Eintrag" not in str(p)]
(ROOT / "katalog.json").write_text(json.dumps(current, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

codes = {c for e in vb_new + urban for c in e.get("codes", [])}
print(f"restored urban={len(urban)}, total vb={len(vb_new)+len(urban)}, unique codes={len(codes)}")
