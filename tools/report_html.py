"""Generate pruefliste.html (styled, standalone) from katalog data."""
import html, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = r"C:\Users\Mirsad.Karasalihovic\Desktop\Mustertafeln-Katalog"

d = json.load(open(os.path.join(HERE, "katalog.json"), encoding="utf-8"))
entries, checklist, problems = d["entries"], d["checklist"], d["problems"]

by_page = {}
for e in entries:
    by_page.setdefault(e["seite"], []).append(e)

rows = []
for ck in checklist:
    p = ck["page"]
    es = by_page.get(p, [])
    serie = html.escape(ck.get("serie") or "")
    if es:
        cell = "<br>".join(
            html.escape(", ".join(e["codes"]) if e["codes"] else (e.get("name") or e["id"]))
            + (" <span class='man'>manuell</span>" if e.get("manuell") else "")
            + (" <span class='warn'>unklar</span>" if e.get("unklar") else "")
            for e in es)
        typ = ""
    else:
        cell = "–"
        typ = html.escape(ck.get("typ") or "")
    rows.append(f"<tr><td class='pg'>{p}</td><td>{serie}</td><td>{cell}"
                + (f" <span class='typ'>{typ}</span>" if typ else "") + "</td></tr>")

probs = "".join(
    f"<li><b>Seite {pr['page']}</b>"
    + (f" ({html.escape(', '.join(pr.get('codes', [])))})" if pr.get("codes") else "")
    + f": {html.escape(pr['grund'])}</li>"
    for pr in problems)

n_man = sum(1 for e in entries if e.get("manuell"))
doc = f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Prüfliste · Mustertafeln engers</title>
<style>
body{{font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  color:#1c1c1e;background:#f4f3f0;margin:0;padding:24px}}
main{{max-width:900px;margin:0 auto}}
h1{{font-family:Georgia,serif;font-size:26px;margin:0 0 4px}}
h2{{font-size:17px;margin:28px 0 10px}}
.sub{{color:#75757a;margin-bottom:20px}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;
  overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
th{{text-align:left;background:#2d2d30;color:#fff;padding:8px 12px;font-size:12.5px;
  text-transform:uppercase;letter-spacing:.06em}}
td{{padding:7px 12px;border-bottom:1px solid #eceae5;vertical-align:top}}
tr:nth-child(even) td{{background:#faf9f7}}
.pg{{font-weight:700;white-space:nowrap;width:52px}}
.man{{background:#e3ecdf;color:#3c6b2f;border-radius:6px;padding:1px 6px;font-size:11px}}
.warn{{background:#fdf3e4;color:#8a5b12;border-radius:6px;padding:1px 6px;font-size:11px}}
.typ{{color:#75757a;font-style:italic;font-size:12.5px}}
ul.pr{{background:#fff;border-radius:10px;padding:14px 14px 14px 32px;
  box-shadow:0 1px 3px rgba(0,0,0,.08)}}
ul.pr li{{margin:4px 0}}
</style></head><body><main>
<h1>Prüfliste: Mustertafeln engers.pdf → Digitaler Katalog</h1>
<div class="sub"><b>{len(entries)} Tafel-Einträge</b> aus 261 PDF-Seiten · {n_man} davon manuell erfasst/verifiziert · Stand 06.07.2026</div>
<h2>Unklare / besondere Punkte</h2>
<ul class="pr">{probs or "<li>keine</li>"}</ul>
<h2>Seite → gefundene Tafeln</h2>
<table><tr><th>Seite</th><th>Serie</th><th>Erfasste Tafeln / Typ</th></tr>
{"".join(rows)}
</table></main></body></html>"""

out = os.path.join(PROJ, "pruefliste.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(doc)
print("written", out, len(doc), "bytes")
