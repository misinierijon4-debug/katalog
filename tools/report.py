"""Write pruefliste.md + katalog.json into the project folder."""
import json, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = r"C:\Users\Mirsad.Karasalihovic\Desktop\Mustertafeln-Katalog"

d = json.load(open(os.path.join(HERE, "katalog.json"), encoding="utf-8"))
entries, checklist, problems = d["entries"], d["checklist"], d["problems"]

by_page = {}
for e in entries:
    by_page.setdefault(e["seite"], []).append(e)

lines = ["# Prüfliste: Mustertafeln engers.pdf → Digitaler Katalog", ""]
lines.append(f"**{len(entries)} Tafel-Einträge** aus 261 PDF-Seiten "
             f"({sum(1 for e in entries if e.get('manuell'))} davon manuell erfasst/verifiziert).")
lines.append("")
lines.append("| Seite | Serie | Erfasste Tafeln / Typ |")
lines.append("|---|---|---|")
for ck in checklist:
    p = ck["page"]
    es = by_page.get(p, [])
    if es:
        codes = "<br>".join(", ".join(e["codes"]) if e["codes"] else (e.get("name") or e["id"])
                             for e in es)
        typ = ""
    else:
        codes = "–"
        typ = ck.get("typ") or ""
    serie = ck.get("serie") or ""
    lines.append(f"| {p} | {serie} | {codes} {('· *' + typ + '*') if typ else ''} |")

lines.append("")
lines.append("## Unklare / besondere Punkte")
if problems:
    for pr in problems:
        codes = ", ".join(pr.get("codes", [])) if pr.get("codes") else ""
        lines.append(f"- **Seite {pr['page']}**{(' (' + codes + ')') if codes else ''}: {pr['grund']}")
else:
    lines.append("- keine")

with open(os.path.join(PROJ, "pruefliste.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

# JSON-Datenbasis ins Projekt
slim = {"quelle": "Mustertafeln engers.pdf (261 Seiten)",
        "einträge": entries, "probleme": problems}
with open(os.path.join(PROJ, "katalog.json"), "w", encoding="utf-8") as f:
    json.dump(slim, f, ensure_ascii=False, indent=1)

n_pages_with = len(by_page)
print("pages with entries:", n_pages_with, "| entries:", len(entries))
print("written: pruefliste.md, katalog.json")
