"""Build auftraege.html = exact copy of index.html + Auftragsverwaltung.

index.html is never modified. The addon (CSS/HTML/JS) is spliced in at fixed
anchors, so this script can be re-run after every catalog rebuild:

    uv run --python 3.12 python tools/build_auftraege.py
"""
import os, re

PROJ = r"C:\Users\Mirsad.Karasalihovic\Desktop\Mustertafeln-Katalog"

CSS = r"""
/* ---------- Auftragsverwaltung ---------- */
#afBar{background:var(--card);border-bottom:1px solid var(--line);padding:8px 16px}
.af-hrow{max-width:1400px;margin:0 auto;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.af-btn{border:0;background:var(--badge);color:#fff;border-radius:999px;min-height:40px;
  padding:8px 16px;font-size:13.5px;cursor:pointer;display:inline-flex;gap:7px;align-items:center}
.af-btn:hover{background:#000}
.af-btn.sec{background:var(--chip);color:var(--ink)}
.af-btn.sec:hover{background:#dedcd5}
.af-btn.acc{background:var(--accent)}
.af-btn.acc:hover{background:#8f2422}
.af-toggle{font-weight:700;background:transparent;border:0;font-size:15px;cursor:pointer;
  min-height:40px;display:inline-flex;align-items:center;gap:8px;color:var(--ink)}
.af-count{background:var(--accent);color:#fff;border-radius:999px;font-size:12px;font-weight:700;padding:2px 9px}
#afList{max-width:1400px;margin:8px auto 4px;display:flex;flex-direction:column;gap:8px}
.af-row{background:var(--bg);border:1px solid var(--line);border-radius:12px;padding:10px 12px;
  display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.af-row.done{opacity:.62}
.af-nr{font-weight:700;font-size:15px}
.af-meta{color:var(--muted);font-size:13px}
.af-prog{background:var(--chip);border-radius:8px;padding:4px 10px;font-size:13px;font-weight:600}
.af-status{border-radius:999px;padding:4px 10px;font-size:12px;font-weight:700}
.af-status.offen{background:#fdf3e4;color:#8a5b12}
.af-status.erledigt{background:#e4f3e6;color:#1e6b2a}
.af-rowbtns{margin-left:auto;display:flex;gap:6px;flex-wrap:wrap}
.af-empty{color:var(--muted);font-size:13.5px;padding:6px 2px}
/* Hinweis-Balken aktiver Auftrag */
#afBanner{background:var(--badge);color:#fff;border-radius:var(--radius);padding:12px 16px;
  margin:0 0 14px;display:flex;gap:10px;align-items:center;flex-wrap:wrap;box-shadow:var(--shadow)}
#afBanner b{font-size:16px}
#afBanner .af-prog{background:rgba(255,255,255,.16);color:#fff}
.af-unk{background:var(--accent);color:#fff;border-radius:999px;padding:6px 12px;font-size:12.5px;
  cursor:pointer;display:inline-flex;gap:6px;align-items:center;min-height:40px;border:0}
.af-unk.done{background:#5c5c60;text-decoration:line-through}
/* Karten-Dekoration */
.af-stk{position:absolute;top:8px;left:8px;background:var(--accent);color:#fff;font-size:12px;
  font-weight:700;padding:4px 9px;border-radius:999px;box-shadow:0 2px 6px rgba(0,0,0,.25)}
.af-stk.shift{top:36px}
.af-chk{position:absolute;bottom:8px;left:8px;background:rgba(255,255,255,.94);border-radius:999px;
  padding:6px 12px;font-size:12.5px;font-weight:600;display:inline-flex;gap:6px;align-items:center;
  cursor:pointer;box-shadow:0 1px 5px rgba(0,0,0,.3);min-height:40px}
.af-chk input{width:18px;height:18px;accent-color:var(--accent);cursor:pointer}
.card.af-done{opacity:.45}
.card.af-done .thumbbox img{filter:grayscale(.8)}
/* Overlays (Editor / Druckliste) */
.af-overlay{position:fixed;inset:0;background:rgba(20,20,22,.55);z-index:120;display:none;
  align-items:flex-start;justify-content:center;padding:18px;overflow:auto;
  backdrop-filter:blur(3px);-webkit-backdrop-filter:blur(3px)}
.af-overlay.open{display:flex}
.af-dlg{background:var(--card);border-radius:18px;max-width:860px;width:100%;box-shadow:var(--shadow-lg);
  padding:20px;position:relative;margin:auto 0}
.af-dlg h2{margin:0 0 14px;font-family:Georgia,serif;font-size:21px}
.af-dlg .sect{margin-top:14px}
.af-x{position:absolute;top:10px;right:10px;border:0;background:var(--chip);width:40px;height:40px;
  border-radius:50%;font-size:16px;cursor:pointer}
.af-form{display:flex;gap:10px;flex-wrap:wrap}
.af-form label{display:flex;flex-direction:column;gap:4px;font-size:12.5px;color:var(--muted);flex:1;min-width:150px}
.af-form input{padding:10px 12px;border:1px solid var(--line);border-radius:10px;font-size:15px;
  background:var(--bg);outline:none;min-height:40px}
.af-form input:focus{border-color:#b8b5ae}
table.af-pos{width:100%;border-collapse:collapse;font-size:13.5px;margin-top:6px}
table.af-pos th{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.08em;
  color:var(--muted);padding:4px 6px 6px 0;border-bottom:1px solid var(--line)}
table.af-pos td{padding:7px 6px 7px 0;border-bottom:1px dashed var(--line);vertical-align:middle}
table.af-pos input{padding:8px 10px;border:1px solid var(--line);border-radius:8px;font-size:13.5px;
  background:var(--bg);width:100%;min-height:40px}
table.af-pos input.stk{width:64px;text-align:center}
.af-ok{color:#1e6b2a;font-weight:600;white-space:nowrap}
.af-bad{color:var(--accent);font-weight:700;white-space:nowrap}
.af-del{border:0;background:var(--chip);border-radius:50%;width:40px;height:40px;cursor:pointer;font-size:14px}
.af-del:hover{background:var(--accent);color:#fff}
/* Autocomplete */
.af-acwrap{position:relative;flex:1;min-width:220px}
.af-acwrap input{width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:10px;
  font-size:15px;background:var(--bg);outline:none;min-height:44px}
.af-aclist{position:absolute;top:100%;left:0;right:0;background:var(--card);border:1px solid var(--line);
  border-radius:10px;box-shadow:var(--shadow-lg);z-index:10;max-height:280px;overflow:auto;display:none}
.af-aclist.open{display:block}
.af-aclist button{display:block;width:100%;text-align:left;border:0;background:transparent;cursor:pointer;
  padding:10px 12px;font-size:13.5px;border-bottom:1px dashed var(--line);min-height:40px}
.af-aclist button:hover,.af-aclist button.sel{background:var(--chip)}
.af-aclist .m{color:var(--muted);font-size:12px}
#afTa{width:100%;min-height:120px;border:1px solid var(--line);border-radius:10px;background:var(--bg);
  padding:10px 12px;font:13px/1.5 ui-monospace,Consolas,monospace;resize:vertical;outline:none}
.af-note{font-size:12.5px;color:var(--muted)}
.af-footbtns{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px;justify-content:flex-end}
/* Druckliste */
.af-plist{display:flex;flex-direction:column;gap:6px;margin-top:10px}
.af-prow{display:flex;gap:10px;align-items:center;background:var(--bg);border:1px solid var(--line);
  border-radius:10px;padding:8px 12px}
.af-prow.done{opacity:.5}
/* OCR */
#afOcrZone{border:2px dashed var(--line);border-radius:12px;background:var(--bg);padding:16px;
  display:flex;gap:10px;align-items:center;flex-wrap:wrap;transition:border-color .15s,background .15s}
#afOcrZone.drag{border-color:var(--accent);background:#fbeeee}
#afOcrProg{display:none;align-items:center;gap:10px;flex-wrap:wrap;margin-top:8px}
.af-pbar{flex:1;min-width:160px;height:10px;background:var(--chip);border-radius:999px;overflow:hidden}
.af-pbar i{display:block;height:100%;width:0;background:var(--accent);border-radius:999px;transition:width .2s}
#afOcrRaw{display:none;max-height:200px;overflow:auto;background:var(--bg);border:1px solid var(--line);
  border-radius:10px;padding:10px 12px;font:12px/1.5 ui-monospace,Consolas,monospace;white-space:pre-wrap;margin-top:8px}
.af-conf{display:inline-block;width:12px;height:12px;border-radius:50%;vertical-align:-1px;margin-right:5px}
.af-conf.g{background:#2e9e44}.af-conf.y{background:#e0a410}.af-conf.r{background:#c93434}
.af-sugg{border:1px dashed var(--accent);background:transparent;color:var(--accent);border-radius:999px;
  padding:5px 11px;font-size:12.5px;cursor:pointer;margin:2px 4px 0 0;min-height:36px}
.af-sugg:hover{background:var(--accent);color:#fff}
.af-fixnote{font-size:11.5px;color:var(--muted)}
/* Toast */
#afToast{position:fixed;bottom:18px;left:50%;transform:translateX(-50%);background:var(--badge);color:#fff;
  border-radius:12px;padding:12px 18px;font-size:13.5px;z-index:300;box-shadow:var(--shadow-lg);
  display:none;max-width:90vw;text-align:center}
@media (max-width:720px){
  .af-dlg{padding:14px}
  .af-rowbtns{margin-left:0;width:100%}
  table.af-pos .hidem{display:none}
}
"""

BAR = r"""
<div id="afBar">
  <div class="af-hrow">
    <button class="af-toggle" id="afToggle">▸ 📋 Aufträge <span class="af-count" id="afN">0</span></button>
    <button class="af-btn" id="afNew">+ Neuer Auftrag</button>
    <button class="af-btn sec" id="afExpAll" title="Alle Aufträge als JSON-Datei sichern">⬇ Export JSON</button>
    <button class="af-btn sec" id="afImp" title="Aufträge aus JSON-Datei laden">⬆ Import JSON</button>
    <input type="file" id="afImpFile" accept=".json,application/json" style="display:none">
  </div>
  <div id="afList" style="display:none"></div>
</div>
"""

BANNER = r"""<div id="afBanner" style="display:none"></div>"""

DIALOGS = r"""
<div class="af-overlay" id="afEditOv">
  <div class="af-dlg">
    <button class="af-x" data-close="afEditOv">✕</button>
    <h2 id="afEditTitle">Neuer Auftrag</h2>
    <div class="af-form">
      <label>Auftragsnummer *<input id="afFnr" autocomplete="off" placeholder="z.B. 168546"></label>
      <label>Kunde<input id="afFkunde" autocomplete="off" placeholder="Name / Firma"></label>
      <label>Datum<input id="afFdatum" type="date"></label>
    </div>
    <div class="sect">Positionen</div>
    <table class="af-pos"><thead><tr><th>Code</th><th>Stück</th><th class="hidem">Notiz</th><th>Katalog</th><th></th></tr></thead>
      <tbody id="afPosBody"></tbody></table>
    <div class="af-form" style="margin-top:10px">
      <div class="af-acwrap">
        <input id="afAc" autocomplete="off" placeholder="Code suchen und hinzufügen … (z.B. 9552 IR80)">
        <div class="af-aclist" id="afAcList"></div>
      </div>
    </div>
    <div class="sect">Text-Import</div>
    <textarea id="afTa" placeholder="Auftragstext hier einfügen (z.B. aus Scan/E-Mail) – Codes wie 9552-IR80-0C-10 werden automatisch erkannt, auch ohne Bindestriche."></textarea>
    <div class="af-footbtns" style="justify-content:flex-start;margin-top:8px">
      <button class="af-btn sec" id="afAnalyze">Text analysieren</button>
      <span class="af-note" id="afTaInfo"></span>
    </div>
    <div class="sect">Foto scannen (OCR)</div>
    <div id="afOcrZone">
      <button class="af-btn" id="afOcrPick">📷 Foto aufnehmen / auswählen</button>
      <span class="af-note">… oder Bild hierher ziehen. Mehrere Fotos nacheinander möglich (mehrseitige Aufträge).</span>
      <input type="file" id="afOcrFile" accept="image/*" capture="environment" multiple style="display:none">
    </div>
    <div id="afOcrProg">
      <span class="af-note" id="afOcrStat">–</span>
      <div class="af-pbar"><i id="afOcrBar"></i></div>
      <button class="af-btn sec" id="afOcrCancel">✕ Abbrechen</button>
    </div>
    <div class="af-note" style="margin-top:6px">🔒 Die Bilder werden ausschließlich lokal im Browser verarbeitet und verlassen das Gerät nicht.
      <span id="afOcrNet" style="display:none;color:var(--accent);font-weight:700"> OCR benötigt Internet (lokale OCR-Dateien nicht gefunden).</span></div>
    <div class="af-footbtns" style="justify-content:flex-start;margin-top:6px">
      <button class="af-btn sec" id="afOcrRawBtn" style="display:none">Rohtext anzeigen</button>
    </div>
    <pre id="afOcrRaw"></pre>
    <div id="afPrevWrap" style="display:none">
      <div class="sect">Vorschau – erkannte Positionen prüfen</div>
      <table class="af-pos"><thead><tr><th>Übernehmen</th><th>Code</th><th>Stück</th><th>Katalog-Treffer</th></tr></thead>
        <tbody id="afPrevBody"></tbody></table>
      <div class="af-footbtns" style="justify-content:flex-start">
        <button class="af-btn" id="afPrevTake">Positionen übernehmen</button>
        <button class="af-btn sec" id="afPrevDrop">Vorschau verwerfen</button>
      </div>
    </div>
    <div class="af-footbtns">
      <button class="af-btn sec" data-close="afEditOv">Abbrechen</button>
      <button class="af-btn acc" id="afSaveBtn">💾 Auftrag speichern</button>
    </div>
  </div>
</div>

<div class="af-overlay" id="afPrintOv">
  <div class="af-dlg" style="max-width:520px">
    <button class="af-x" data-close="afPrintOv">✕</button>
    <h2>Alle Seiten drucken</h2>
    <div class="af-note" id="afPrintInfo"></div>
    <div class="af-plist" id="afPrintList"></div>
    <div class="af-footbtns">
      <button class="af-btn" id="afPrintSeq">▶ Nacheinander drucken</button>
      <button class="af-btn sec" data-close="afPrintOv">Schließen</button>
    </div>
  </div>
</div>
<div id="afToast"></div>
"""

JS = r"""
/* ================== Auftragsverwaltung ================== */
const AF_KEY="auftraege_v1";
const afById=Object.fromEntries(DATA.map(e=>[e.id,e]));
const afNormCode=s=>(s||"").toString().toUpperCase().replace(/[^A-Z0-9]/g,"");
const AF_CODEMAP={};
DATA.forEach(e=>(e.codes||[]).forEach(c=>{const k=afNormCode(c);(AF_CODEMAP[k]=AF_CODEMAP[k]||[]).push(e.id);}));
const AF_CODES=[];
{const seen=new Set();
 DATA.forEach(e=>(e.codes||[]).forEach(c=>{const k=afNormCode(c);if(seen.has(k))return;seen.add(k);
   AF_CODES.push({code:c,norm:k,serie:e.serie||"",seite:e.seite});}));}
function afMatch(code){return AF_CODEMAP[afNormCode(code)]||[];}

let afStoreOk=true, auftraege=[];
try{auftraege=JSON.parse(localStorage.getItem(AF_KEY)||"[]");if(!Array.isArray(auftraege))auftraege=[];}
catch(err){afStoreOk=false;}
function afSave(){
  auftraege.forEach(o=>{const[d,t]=afProg(o);o.status=(t>0&&d===t)?"erledigt":"offen";});
  try{localStorage.setItem(AF_KEY,JSON.stringify(auftraege));}
  catch(err){afToast("⚠️ Speichern fehlgeschlagen (Speicher voll oder blockiert). Bitte Export JSON zur Sicherung nutzen!");}
}
function afProg(o){return [o.positionen.filter(p=>p.erledigt).length,o.positionen.length];}
function afFmtDate(iso){if(!iso)return"–";const m=/^(\d{4})-(\d{2})-(\d{2})/.exec(iso);return m?`${m[3]}.${m[2]}.${m[1]}`:iso;}
let afToastTimer=null;
function afToast(msg){const t=document.getElementById("afToast");t.textContent=msg;t.style.display="block";
  clearTimeout(afToastTimer);afToastTimer=setTimeout(()=>t.style.display="none",4500);}

/* ---------- aktiver Auftrag: Filter- und Render-Hooks ---------- */
let afActive=null, afActiveIds=new Set();
const _afFiltered=filtered;
filtered=function(){let out=_afFiltered();if(afActive)out=out.filter(e=>afActiveIds.has(e.id));return out;};
const _afRender=render;
render=function(){_afRender();afDecorate();afBanner();afList();};

function afOpen(o){
  afActive=o;
  afActiveIds=new Set(o.positionen.flatMap(p=>p.matchIds||[]));
  sort="seite";document.getElementById("sortSel").value="seite";
  q="";document.getElementById("search").value="";document.getElementById("clearBtn").style.display="none";
  serieF="";serieSel.value="";
  typF="";[...chipsBox.children].forEach(x=>x.classList.toggle("on",x.dataset.v===""));
  render();window.scrollTo({top:0,behavior:"smooth"});
}
function afClose(){afActive=null;afActiveIds=new Set();render();}

function afDecorate(){
  if(!afActive)return;
  const list=filtered();
  [...grid.children].forEach((card,i)=>{
    const e=list[i];if(!e)return;
    const poss=afActive.positionen.filter(p=>(p.matchIds||[]).includes(e.id));
    if(!poss.length)return;
    const tb=card.querySelector(".thumbbox");
    const stk=poss.reduce((s,p)=>s+(parseInt(p.stueck)||1),0);
    const sb=el("span","af-stk"+(tb.querySelector(".gtbadge")?" shift":""),stk+" Stk");
    tb.appendChild(sb);
    const done=poss.every(p=>p.erledigt);
    if(done)card.classList.add("af-done");
    const lab=el("label","af-chk");
    const cb=document.createElement("input");cb.type="checkbox";cb.checked=done;
    cb.onchange=()=>{poss.forEach(p=>p.erledigt=cb.checked);afSave();render();};
    lab.appendChild(cb);lab.appendChild(document.createTextNode(" erledigt"));
    lab.onclick=ev=>ev.stopPropagation();
    tb.appendChild(lab);
    const notes=poss.map(p=>p.notiz).filter(Boolean);
    if(notes.length){const nb=card.querySelector(".cbody");
      nb.appendChild(el("div","csize","📝 "+esc(notes.join(" · "))));}
  });
}

function afBanner(){
  const b=document.getElementById("afBanner");
  if(!afActive){b.style.display="none";return;}
  const o=afActive,[d,t]=afProg(o);
  b.style.display="flex";b.innerHTML="";
  b.appendChild(el("b","",`Auftrag ${esc(o.auftragsnr)}`));
  b.appendChild(el("span","",esc(o.kunde||"–")+" · "+afFmtDate(o.datum)));
  b.appendChild(el("span","af-prog",`${t} Positionen · ${d}/${t} erledigt`));
  const unk=o.positionen.filter(p=>!(p.matchIds||[]).length);
  unk.forEach(p=>{
    const u=el("button","af-unk"+(p.erledigt?" done":""),
      "⚠ "+esc(p.code)+" ("+(p.stueck||1)+" Stk) – nicht im Katalog");
    u.title="Klicken zum Abhaken";
    u.onclick=()=>{p.erledigt=!p.erledigt;afSave();render();};
    b.appendChild(u);
  });
  const pr=el("button","af-btn sec","🖨 Alle Seiten drucken");pr.onclick=afPrintAll;
  const cl=el("button","af-btn sec","✕ Auftrag schließen");cl.onclick=afClose;
  const sp=el("span","");sp.style.marginLeft="auto";
  b.appendChild(sp);b.appendChild(pr);b.appendChild(cl);
}

/* ---------- Auftragsliste (Leiste oben) ---------- */
let afBarOpen=false;
function afList(){
  document.getElementById("afN").textContent=auftraege.length;
  document.getElementById("afToggle").firstChild.textContent=(afBarOpen?"▾":"▸")+" 📋 Aufträge ";
  const box=document.getElementById("afList");
  box.style.display=afBarOpen?"flex":"none";
  if(!afBarOpen)return;
  box.innerHTML="";
  if(!auftraege.length){box.appendChild(el("div","af-empty","Noch keine Aufträge. Mit „+ Neuer Auftrag“ anlegen oder JSON importieren."));return;}
  [...auftraege].sort((a,b)=>(b.angelegt||"").localeCompare(a.angelegt||"")).forEach(o=>{
    const[d,t]=afProg(o);
    const r=el("div","af-row"+(o.status==="erledigt"?" done":""));
    r.appendChild(el("span","af-nr",esc(o.auftragsnr)));
    r.appendChild(el("span","af-meta",esc(o.kunde||"–")+" · "+afFmtDate(o.datum)));
    r.appendChild(el("span","af-prog",`${d}/${t} Tafeln`));
    r.appendChild(el("span","af-status "+o.status,o.status));
    const btns=el("div","af-rowbtns");
    const mk=(lbl,cls,fn,title)=>{const x=el("button","af-btn "+cls,lbl);x.onclick=fn;if(title)x.title=title;btns.appendChild(x);};
    mk("Öffnen","",()=>{afOpen(o);});
    mk("Bearbeiten","sec",()=>afEdit(o));
    mk("⬇","sec",()=>afExportOne(o),"Diesen Auftrag als JSON exportieren");
    mk("Löschen","sec",()=>{
      if(confirm(`Auftrag ${o.auftragsnr} wirklich löschen?`)){
        auftraege=auftraege.filter(x=>x!==o);
        if(afActive===o)afClose();
        afSave();render();
      }});
    r.appendChild(btns);
    box.appendChild(r);
  });
}
document.getElementById("afToggle").onclick=()=>{afBarOpen=!afBarOpen;afList();};

/* ---------- Editor ---------- */
let edId=null, edPos=[], edPrev=[];
function afEdit(o){
  edId=o?o.id:null;
  edPos=o?o.positionen.map(p=>({...p,matchIds:afMatch(p.code)})):[];
  edPrev=[];
  document.getElementById("afEditTitle").textContent=o?`Auftrag ${o.auftragsnr} bearbeiten`:"Neuer Auftrag";
  document.getElementById("afFnr").value=o?o.auftragsnr:"";
  document.getElementById("afFkunde").value=o?(o.kunde||""):"";
  document.getElementById("afFdatum").value=o?(o.datum||""):new Date().toISOString().slice(0,10);
  document.getElementById("afTa").value="";document.getElementById("afTaInfo").textContent="";
  afRenderPrev();afRenderPos();
  document.getElementById("afEditOv").classList.add("open");
  document.body.style.overflow="hidden";
}
document.getElementById("afNew").onclick=()=>afEdit(null);

function afRenderPos(){
  const tb=document.getElementById("afPosBody");tb.innerHTML="";
  if(!edPos.length){tb.innerHTML='<tr><td colspan="5" class="af-empty">Noch keine Positionen.</td></tr>';return;}
  edPos.forEach((p,i)=>{
    const tr=document.createElement("tr");
    const tdC=document.createElement("td");
    const ic=document.createElement("input");ic.value=p.code;
    ic.onchange=()=>{p.code=ic.value.trim();p.matchIds=afMatch(p.code);afRenderPos();};
    tdC.appendChild(ic);tr.appendChild(tdC);
    const tdS=document.createElement("td");
    const is=document.createElement("input");is.className="stk";is.type="number";is.min="1";is.value=p.stueck||1;
    is.onchange=()=>{p.stueck=Math.max(1,parseInt(is.value)||1);is.value=p.stueck;};
    tdS.appendChild(is);tr.appendChild(tdS);
    const tdN=document.createElement("td");tdN.className="hidem";
    const inn=document.createElement("input");inn.value=p.notiz||"";inn.placeholder="Notiz";
    inn.onchange=()=>{p.notiz=inn.value.trim();};
    tdN.appendChild(inn);tr.appendChild(tdN);
    const ids=p.matchIds||[];
    tr.appendChild(el("td","",ids.length
      ?`<span class="af-ok">✓ ${ids.length} Tafel${ids.length>1?"n":""}</span> <span class="m" style="color:var(--muted);font-size:12px">${ids.map(id=>"S."+afById[id].seite).join(", ")}</span>`
      :'<span class="af-bad">✗ NICHT im Katalog</span>'));
    const tdX=document.createElement("td");
    const bx=el("button","af-del","✕");bx.title="Position entfernen";
    bx.onclick=()=>{edPos.splice(i,1);afRenderPos();};
    tdX.appendChild(bx);tr.appendChild(tdX);
    tb.appendChild(tr);
  });
}

/* Autocomplete */
const afAc=document.getElementById("afAc"), afAcList=document.getElementById("afAcList");
let acSel=-1;
function afAcRender(){
  const nq=afNormCode(afAc.value);
  afAcList.innerHTML="";acSel=-1;
  if(nq.length<2){afAcList.classList.remove("open");return;}
  const hits=AF_CODES.filter(c=>c.norm.includes(nq)).slice(0,12);
  if(!hits.length){afAcList.classList.remove("open");return;}
  hits.forEach(h=>{
    const b=el("button","",`<b>${esc(h.code)}</b> <span class="m">${esc(h.serie)} · Seite ${h.seite}</span>`);
    b.onmousedown=ev=>{ev.preventDefault();afAddPos(h.code);};
    afAcList.appendChild(b);
  });
  afAcList.classList.add("open");
}
function afAddPos(code){
  edPos.push({code:code,stueck:1,notiz:"",erledigt:false,matchIds:afMatch(code)});
  afAc.value="";afAcList.classList.remove("open");afRenderPos();afAc.focus();
}
afAc.addEventListener("input",afAcRender);
afAc.addEventListener("blur",()=>setTimeout(()=>afAcList.classList.remove("open"),150));
afAc.addEventListener("keydown",ev=>{
  const btns=[...afAcList.children];
  if(ev.key==="ArrowDown"&&btns.length){ev.preventDefault();acSel=Math.min(acSel+1,btns.length-1);btns.forEach((b,i)=>b.classList.toggle("sel",i===acSel));}
  if(ev.key==="ArrowUp"&&btns.length){ev.preventDefault();acSel=Math.max(acSel-1,0);btns.forEach((b,i)=>b.classList.toggle("sel",i===acSel));}
  if(ev.key==="Enter"){ev.preventDefault();
    if(acSel>=0&&btns[acSel]){btns[acSel].onmousedown(ev);}
    else if(afNormCode(afAc.value).length>=8){afAddPos(afAc.value.trim());}
    else if(afAc.value.trim()){afToast("Code zu kurz – bitte aus der Liste wählen oder vollständigen Code eingeben.");}}
});

/* Text-Import (+ OCR-Nachbearbeitung: Verwechslungs-Korrektur, Fuzzy-Vorschläge, Konfidenz) */
const AF_CODE_RE=/(\d{4})[\s-]*([A-Za-z][A-Za-z0-9]{3})[\s-]*([A-Za-z0-9]{2})[\s-]*(\d{2})/g;
/* lockere Variante für OCR: in Ziffern-Gruppen auch typische Buchstaben-Verwechslungen zulassen */
const AF_CODE_LOOSE=/([0-9OIlSBZG]{4})[\s\-.]*([A-Za-z0-9]{4})[\s\-.]*([A-Za-z0-9]{2})[\s\-.]*([0-9OIlSBZG]{2})/g;
const AF_L2D={O:"0",Q:"0",D:"0",I:"1",L:"1",S:"5",B:"8",Z:"2",G:"6"};
const AF_ALT={O:["0"],Q:["0"],D:["0"],I:["1"],L:["1"],S:["5"],B:["8"],Z:["2"],G:["6"],
  "0":["O","D"],"1":["I","L"],"5":["S"],"8":["B"],"2":["Z"],"6":["G"]};
function afCoerce(raw){ /* Ziffern-Gruppen (Pos 0-3, 10-11) hart koerzieren */
  const n=afNormCode(raw);
  if(n.length!==12)return n;
  const a=n.split("");
  for(const i of[0,1,2,3,10,11])if(AF_L2D[a[i]])a[i]=AF_L2D[a[i]];
  return a.join("");
}
function afResolveCode(raw){ /* -> exakter Katalog-Norm-Code oder null */
  const n=afNormCode(raw);
  if(AF_CODEMAP[n])return n;
  if(n.length!==12)return null;
  const co=afCoerce(n);
  if(AF_CODEMAP[co])return co;
  /* mittlere Gruppen (Pos 4-9): ambivalente Zeichen in allen Varianten durchprobieren */
  let cands=[co];
  for(let i=4;i<=9;i++){
    const next=[];
    for(const c of cands){
      next.push(c);
      (AF_ALT[c[i]]||[]).forEach(alt=>next.push(c.slice(0,i)+alt+c.slice(i+1)));
    }
    cands=next.slice(0,256);
  }
  for(const c of cands)if(AF_CODEMAP[c])return c;
  return null;
}
function afLev(a,b,max){ /* Levenshtein mit Abbruch > max */
  if(Math.abs(a.length-b.length)>max)return max+1;
  let prev=[...Array(b.length+1).keys()];
  for(let i=1;i<=a.length;i++){
    const cur=[i];let best=i;
    for(let j=1;j<=b.length;j++){
      cur[j]=Math.min(prev[j]+1,cur[j-1]+1,prev[j-1]+(a[i-1]===b[j-1]?0:1));
      best=Math.min(best,cur[j]);
    }
    if(best>max)return max+1;
    prev=cur;
  }
  return prev[b.length];
}
function afFuzzy(raw){ /* Vorschläge mit Distanz <= 2, nie automatisch übernehmen */
  const n=afCoerce(raw);
  return AF_CODES.map(c=>({c,d:afLev(n,c.norm,2)})).filter(x=>x.d<=2)
    .sort((x,y)=>x.d-y.d).slice(0,3).map(x=>x.c.code);
}
function afCanon(normOrRaw){ /* Katalog-Schreibweise zu einem Norm-Code */
  const ids=afMatch(normOrRaw);
  if(!ids.length)return null;
  const e=afById[ids[0]];
  return (e.codes||[]).find(c=>afNormCode(c)===afNormCode(normOrRaw))||e.codes[0];
}
function afQty(rest,isOcr){
  let mm;
  if((mm=rest.match(/(\d{1,3})\s*(?:x(?!\s*\d)|stk\.?|st(?:ü|ue)ck\b|\bST\b)/i)))return +mm[1];
  if((mm=rest.match(/(?:(?<![0-9])x|stk\.?|st(?:ü|ue)ck|menge)[.:\s]*(\d{1,3})\b/i)))return +mm[1];
  if((mm=rest.match(/(?:^|\s)(\d{1,3})\s*$/)))return +mm[1]; /* Zahl am Zeilenende */
  return isOcr?"":1; /* OCR: bei Unsicherheit leer lassen statt raten */
}
function afAnalyze(){
  const txt=document.getElementById("afTa").value;
  edPrev=[];
  const lines=txt.split(/\r?\n/);
  lines.forEach(line=>{
    const conf=afOcrConf[afLineKey(line)];
    const isOcr=conf!==undefined;
    const strict=[...line.matchAll(AF_CODE_RE)];
    const loose=isOcr?[...line.matchAll(AF_CODE_LOOSE)]
      .filter(m=>!strict.some(s=>m.index<s.index+s[0].length&&s.index<m.index+m[0].length)):[];
    const found=[...strict.map(m=>({m,loose:false})),...loose.map(m=>({m,loose:true}))];
    if(!found.length)return;
    let rest=line;
    found.forEach(f=>{rest=rest.replace(f.m[0],"");});
    const stk=afQty(rest,isOcr);
    found.forEach(f=>{
      const m=f.m;
      const raw=(m[1]+"-"+m[2]+"-"+m[3]+"-"+m[4]).toUpperCase();
      const resolved=afResolveCode(raw);
      let sugg=[];
      if(!resolved){
        sugg=afFuzzy(raw);
        if(f.loose&&!sugg.length)return; /* lockerer Treffer ohne jeden Katalog-Bezug = Rauschen */
      }
      const row={code:resolved?afCanon(resolved):raw,stueck:stk,keep:true,line:line.trim(),conf:conf,sugg:sugg};
      if(resolved&&afNormCode(raw)!==resolved)row.fixed=raw;
      edPrev.push(row);
    });
  });
  document.getElementById("afTaInfo").textContent=edPrev.length
    ?`${edPrev.length} Code(s) erkannt – bitte unten prüfen.`
    :"Keine Tafel-Codes im Text gefunden.";
  afRenderPrev();
}
document.getElementById("afAnalyze").onclick=afAnalyze;
function afRenderPrev(){
  const wrap=document.getElementById("afPrevWrap");
  wrap.style.display=edPrev.length?"block":"none";
  const tb=document.getElementById("afPrevBody");tb.innerHTML="";
  edPrev.forEach(r=>{
    const ids=afMatch(r.code);
    const tr=document.createElement("tr");
    const tdK=document.createElement("td");
    const ck=document.createElement("input");ck.type="checkbox";ck.checked=r.keep;
    ck.style.cssText="width:20px;height:20px;accent-color:var(--accent)";
    ck.onchange=()=>{r.keep=ck.checked;};
    tdK.appendChild(ck);tr.appendChild(tdK);
    const tdC=document.createElement("td");
    const ic=document.createElement("input");ic.value=r.code;ic.title=r.line;
    ic.onchange=()=>{r.code=ic.value.trim();afRenderPrev();};
    tdC.appendChild(ic);
    if(r.fixed)tdC.appendChild(el("div","af-fixnote","korrigiert aus "+esc(r.fixed)));
    tr.appendChild(tdC);
    const tdS=document.createElement("td");
    const is=document.createElement("input");is.className="stk";is.type="number";is.min="1";is.value=r.stueck;
    is.placeholder="?";
    is.onchange=()=>{r.stueck=is.value===""?"":Math.max(1,parseInt(is.value)||1);is.value=r.stueck;};
    tdS.appendChild(is);tr.appendChild(tdS);
    const tdM=document.createElement("td");
    let dot="";
    if(r.conf!==undefined){
      const cls=r.conf>=85?"g":(r.conf>=60?"y":"r");
      dot=`<span class="af-conf ${cls}" title="OCR-Konfidenz ${Math.round(r.conf)}%"></span>`;
    }
    if(ids.length){
      tdM.innerHTML=dot+`<span class="af-ok">✓ ${ids.map(id=>{const e=afById[id];return esc((e.serie||"")+" S."+e.seite);}).join(", ")}</span>`;
    }else{
      tdM.innerHTML=dot+'<span class="af-bad">✗ NICHT im Katalog</span>';
      (r.sugg||[]).forEach(s=>{
        const b=el("button","af-sugg","Meintest du "+esc(s)+"?");
        b.onclick=()=>{r.code=s;r.sugg=[];afRenderPrev();};
        tdM.appendChild(document.createElement("br"));
        tdM.appendChild(b);
      });
    }
    tr.appendChild(tdM);
    tb.appendChild(tr);
  });
}
document.getElementById("afPrevTake").onclick=()=>{
  const take=edPrev.filter(r=>r.keep);
  take.forEach(r=>edPos.push({code:r.code,stueck:parseInt(r.stueck)||1,notiz:"",erledigt:false,matchIds:afMatch(r.code)}));
  const dropped=edPrev.length-take.length;
  edPrev=[];document.getElementById("afTa").value="";document.getElementById("afTaInfo").textContent="";
  afRenderPrev();afRenderPos();
  afToast(`${take.length} Position(en) übernommen${dropped?`, ${dropped} bewusst verworfen`:""}.`);
};
document.getElementById("afPrevDrop").onclick=()=>{edPrev=[];afRenderPrev();};

/* Speichern */
document.getElementById("afSaveBtn").onclick=()=>{
  const nr=document.getElementById("afFnr").value.trim();
  if(!nr){afToast("Bitte Auftragsnummer eingeben.");return;}
  if(edPrev.length&&!confirm("Die Text-Import-Vorschau wurde noch nicht übernommen und geht verloren. Trotzdem speichern?"))return;
  if(!edId&&auftraege.some(o=>o.auftragsnr===nr)
     &&!confirm(`Ein Auftrag mit Nummer ${nr} existiert bereits. Trotzdem als zusätzlichen Auftrag speichern?`))return;
  edPos.forEach(p=>{p.matchIds=afMatch(p.code);});
  if(edId){
    const o=auftraege.find(x=>x.id===edId);
    Object.assign(o,{auftragsnr:nr,kunde:document.getElementById("afFkunde").value.trim(),
      datum:document.getElementById("afFdatum").value,positionen:edPos});
    if(afActive&&afActive.id===edId)afOpen(o);
  }else{
    const o={id:"a"+Date.now().toString(36)+Math.random().toString(36).slice(2,6),
      auftragsnr:nr,kunde:document.getElementById("afFkunde").value.trim(),
      datum:document.getElementById("afFdatum").value,angelegt:new Date().toISOString(),
      positionen:edPos,status:"offen"};
    auftraege.push(o);
  }
  afSave();afBarOpen=true;
  document.getElementById("afEditOv").classList.remove("open");document.body.style.overflow="";
  render();afToast(`Auftrag ${nr} gespeichert (${edPos.length} Positionen).`);
  if(!afStoreOk)afToast("⚠️ Hinweis: localStorage nicht verfügbar – Auftrag geht beim Schließen verloren. Bitte Export JSON nutzen.");
};

/* ---------- Sammeldruck ---------- */
function afPrintAll(){
  if(!afActive)return;
  const pages=[...new Set(afActive.positionen.flatMap(p=>(p.matchIds||[]).map(id=>afById[id].seite)))].sort((a,b)=>a-b);
  const info=document.getElementById("afPrintInfo");
  info.textContent=pages.length
    ?`${pages.length} Katalogseite(n) für Auftrag ${afActive.auftragsnr}. Einzeln drucken oder nacheinander (der Browser kann Mehrfach-Dialoge blockieren – dann bitte einzeln abhaken).`
    :"Keine Katalogseiten – der Auftrag enthält nur unbekannte Codes.";
  const listBox=document.getElementById("afPrintList");listBox.innerHTML="";
  pages.forEach(pn=>{
    const row=el("div","af-prow");
    const b=el("button","af-btn","🖨 Seite "+pn);
    b.onclick=()=>{printPage(pn);row.classList.add("done");};
    row.appendChild(b);
    row.appendChild(el("span","af-note",pdfUrl(pn)));
    listBox.appendChild(row);
  });
  const seq=document.getElementById("afPrintSeq");
  seq.style.display=pages.length?"":"none";
  seq.onclick=()=>{
    pages.forEach((pn,i)=>setTimeout(()=>{
      printPage(pn);
      const r=listBox.children[i];if(r)r.classList.add("done");
    },i*2200));
  };
  document.getElementById("afPrintOv").classList.add("open");
  document.body.style.overflow="hidden";
}

/* ---------- Export / Import JSON ---------- */
function afDownload(obj,name){
  const blob=new Blob([JSON.stringify(obj,null,1)],{type:"application/json"});
  const a=document.createElement("a");
  a.href=URL.createObjectURL(blob);a.download=name;
  document.body.appendChild(a);a.click();
  setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove();},500);
}
function afExportOne(o){afDownload(o,`auftrag_${(o.auftragsnr||"x").replace(/[^\w.-]+/g,"_")}_${o.datum||"ohne-datum"}.json`);}
document.getElementById("afExpAll").onclick=()=>{
  if(!auftraege.length){afToast("Keine Aufträge zum Exportieren.");return;}
  afDownload(auftraege,`auftraege_${new Date().toISOString().slice(0,10)}.json`);
};
document.getElementById("afImp").onclick=()=>document.getElementById("afImpFile").click();
document.getElementById("afImpFile").addEventListener("change",ev=>{
  const f=ev.target.files[0];ev.target.value="";
  if(!f)return;
  const rd=new FileReader();
  rd.onload=()=>{
    let arr;
    try{arr=JSON.parse(rd.result);}catch(err){afToast("⚠️ Datei ist kein gültiges JSON.");return;}
    if(!Array.isArray(arr))arr=[arr];
    let ok=0;
    for(const raw of arr){
      if(!raw||typeof raw!=="object"||!raw.auftragsnr||!Array.isArray(raw.positionen)){
        afToast("⚠️ Eintrag ohne auftragsnr/positionen übersprungen.");continue;}
      const o={id:raw.id||("a"+Date.now().toString(36)+Math.random().toString(36).slice(2,6)),
        auftragsnr:String(raw.auftragsnr),kunde:raw.kunde||"",datum:raw.datum||"",
        angelegt:raw.angelegt||new Date().toISOString(),status:raw.status||"offen",
        positionen:raw.positionen.map(p=>({code:String(p.code||""),stueck:parseInt(p.stueck)||1,
          notiz:p.notiz||"",erledigt:!!p.erledigt,matchIds:afMatch(p.code)}))};
      const ex=auftraege.find(x=>x.id===o.id||x.auftragsnr===o.auftragsnr);
      if(ex){
        if(confirm(`Auftrag ${o.auftragsnr} existiert bereits. Ersetzen?\n(Abbrechen = als Kopie zusätzlich anlegen)`)){
          auftraege[auftraege.indexOf(ex)]=o;
          if(afActive===ex)afClose();
        }else{o.id="a"+Date.now().toString(36)+Math.random().toString(36).slice(2,6);auftraege.push(o);}
      }else auftraege.push(o);
      ok++;
    }
    afSave();afBarOpen=true;render();
    afToast(`${ok} Auftrag/Aufträge importiert.`);
  };
  rd.readAsText(f);
});

/* ---------- OCR: Foto scannen ---------- */
const afOcrConf={};              /* Zeilentext -> OCR-Konfidenz (0..100) */
let afOcrRawAll="", afOcrBusy=false, afOcrCancel=false, afOcrWorker=null;
const afLineKey=s=>(s||"").trim().replace(/\s+/g," ");
const AF_OCR_BASE=new URL("ocr/",location.href).href;
const AF_WHITELIST="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÄÖÜäöüß.,:-/& ";

function afSimd(){ /* WebAssembly-SIMD-Erkennung für Core-Auswahl */
  try{return WebAssembly.validate(new Uint8Array([0,97,115,109,1,0,0,0,1,5,1,96,0,1,123,3,2,1,0,10,10,1,8,0,65,0,253,15,253,98,11]));}
  catch(e){return false;}
}
let afOcrLocal=null; /* null=ungeprüft, true=lokale Dateien, false=CDN */
async function afOcrEnsureLib(){
  if(window.Tesseract)return;
  if(afOcrLocal===null){
    try{const r=await fetch(AF_OCR_BASE+"tesseract.min.js",{method:"HEAD"});afOcrLocal=r.ok;}
    catch(e){afOcrLocal=false;}
  }
  document.getElementById("afOcrNet").style.display=afOcrLocal?"none":"inline";
  const src=afOcrLocal?AF_OCR_BASE+"tesseract.min.js"
    :"https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js";
  await new Promise((res,rej)=>{
    const s=document.createElement("script");
    s.src=src;s.onload=res;
    s.onerror=()=>rej(new Error(afOcrLocal?"ocr/tesseract.min.js nicht ladbar":"Kein Internet – OCR benötigt online die CDN-Dateien."));
    document.head.appendChild(s);
  });
}
async function afOcrMakeWorker(){
  const opts={logger:m=>{
    if(m.status==="recognizing text")afOcrSetBar(Math.round(m.progress*100));
  }};
  if(afOcrLocal){
    opts.workerPath=AF_OCR_BASE+"worker.min.js";
    opts.corePath=AF_OCR_BASE+"tesseract-core-"+(afSimd()?"simd-":"")+"lstm.wasm.js";
    opts.langPath=AF_OCR_BASE.replace(/\/$/,"");
    opts.gzip=true;
  }
  const w=await Tesseract.createWorker("deu+eng",1,opts);
  await w.setParameters({tessedit_pageseg_mode:"6",tessedit_char_whitelist:AF_WHITELIST});
  return w;
}
function afOcrSetBar(p){document.getElementById("afOcrBar").style.width=p+"%";}
function afOcrStat(t){document.getElementById("afOcrStat").textContent=t;}

/* Bildvorverarbeitung: EXIF, Graustufen, Kontrast, Blur, adaptive Binarisierung, <=2500px */
async function afOcrPrep(file){
  let bmp;
  try{bmp=await createImageBitmap(file,{imageOrientation:"from-image"});}
  catch(e){bmp=await createImageBitmap(file);}
  const long=Math.max(bmp.width,bmp.height), f=Math.min(1,2500/long);
  const w=Math.round(bmp.width*f), h=Math.round(bmp.height*f);
  const cv=document.createElement("canvas");cv.width=w;cv.height=h;
  const cx=cv.getContext("2d",{willReadFrequently:true});
  cx.drawImage(bmp,0,0,w,h);bmp.close&&bmp.close();
  const id=cx.getImageData(0,0,w,h),d=id.data,n=w*h;
  const g=new Float32Array(n);
  for(let i=0;i<n;i++)g[i]=0.299*d[i*4]+0.587*d[i*4+1]+0.114*d[i*4+2];
  /* Kontrast: 2%/98%-Perzentile strecken */
  const hist=new Uint32Array(256);
  for(let i=0;i<n;i++)hist[g[i]|0]++;
  let lo=0,hi=255,acc=0;
  for(let v=0;v<256;v++){acc+=hist[v];if(acc>=n*0.02){lo=v;break;}}
  acc=0;for(let v=255;v>=0;v--){acc+=hist[v];if(acc>=n*0.02){hi=v;break;}}
  const span=Math.max(1,hi-lo);
  for(let i=0;i<n;i++)g[i]=Math.max(0,Math.min(255,(g[i]-lo)*255/span));
  /* leichtes 3x3-Blur, damit Nadeldruck-Punkte zu Linien verschmelzen */
  const b=new Float32Array(n);
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){
    let s=0,c=0;
    for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){
      const yy=y+dy,xx=x+dx;
      if(yy>=0&&yy<h&&xx>=0&&xx<w){s+=g[yy*w+xx];c++;}
    }
    b[y*w+x]=s/c;
  }
  /* adaptive Schwellwert-Binarisierung über Integralbild (Fenster 31, C=10) */
  const I=new Float64Array((w+1)*(h+1));
  for(let y=0;y<h;y++){let rs=0;
    for(let x=0;x<w;x++){rs+=b[y*w+x];I[(y+1)*(w+1)+x+1]=I[y*(w+1)+x+1]+rs;}}
  const R=15;
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){
    const x0=Math.max(0,x-R),x1=Math.min(w-1,x+R),y0=Math.max(0,y-R),y1=Math.min(h-1,y+R);
    const area=(x1-x0+1)*(y1-y0+1);
    const sum=I[(y1+1)*(w+1)+x1+1]-I[y0*(w+1)+x1+1]-I[(y1+1)*(w+1)+x0]+I[y0*(w+1)+x0];
    const v=b[y*w+x]<sum/area-10?0:255;
    d[(y*w+x)*4]=d[(y*w+x)*4+1]=d[(y*w+x)*4+2]=v;d[(y*w+x)*4+3]=255;
  }
  cx.putImageData(id,0,0);
  return cv;
}
function afOcrRot(cv,deg){
  if(deg===0)return cv;
  const r=document.createElement("canvas");
  if(deg===180){r.width=cv.width;r.height=cv.height;}
  else{r.width=cv.height;r.height=cv.width;}
  const c=r.getContext("2d");
  c.translate(r.width/2,r.height/2);c.rotate(deg*Math.PI/180);
  c.drawImage(cv,-cv.width/2,-cv.height/2);
  return r;
}
function afOcrSmall(cv,max){
  const f=Math.min(1,max/Math.max(cv.width,cv.height));
  if(f===1)return cv;
  const s=document.createElement("canvas");
  s.width=Math.round(cv.width*f);s.height=Math.round(cv.height*f);
  s.getContext("2d").drawImage(cv,0,0,s.width,s.height);
  return s;
}
/* Kopfdaten (Auftragsnr/Datum/Kunde) vorschlagen – nur leere Felder füllen */
function afOcrHeads(text){
  const noCodes=l=>l.replace(AF_CODE_RE,"");
  for(const l of text.split(/\r?\n/)){
    if(/auftrag/i.test(l)&&!document.getElementById("afFnr").value.trim()){
      const m=noCodes(l).match(/(\d{4,})/);
      if(m)document.getElementById("afFnr").value=m[1];
    }
    if(/kunde/i.test(l)&&!document.getElementById("afFkunde").value.trim()){
      const m=l.match(/kunde[:.\s]*([^\n]{2,60})/i);
      if(m)document.getElementById("afFkunde").value=m[1].replace(/^[^A-Za-zÄÖÜäöü]+/,"").trim();
    }
    const dm=l.match(/\b(\d{1,2})[.,](\d{1,2})[.,](\d{2,4})\b/);
    if(dm&&document.getElementById("afFdatum").dataset.ocrOpen==="1"){
      let[,dd,mo,yy]=dm;if(yy.length===2)yy="20"+yy;
      document.getElementById("afFdatum").value=`${yy}-${mo.padStart(2,"0")}-${dd.padStart(2,"0")}`;
      delete document.getElementById("afFdatum").dataset.ocrOpen;
    }
  }
}
async function afOcrRun(files){
  if(afOcrBusy){afToast("OCR läuft bereits – bitte warten oder abbrechen.");return;}
  afOcrBusy=true;afOcrCancel=false;
  const prog=document.getElementById("afOcrProg");prog.style.display="flex";afOcrSetBar(0);
  /* Datumsfeld nur überschreiben, wenn es noch auf "heute" steht (frischer Dialog) */
  document.getElementById("afFdatum").dataset.ocrOpen="1";
  try{
    afOcrStat("OCR-Modul laden …");
    await afOcrEnsureLib();
    for(let fi=0;fi<files.length;fi++){
      if(afOcrCancel)break;
      const label=`Bild ${fi+1}/${files.length}`;
      afOcrStat(label+" – Vorverarbeitung …");afOcrSetBar(0);
      const cv=await afOcrPrep(files[fi]);
      afOcrWorker=await afOcrMakeWorker();
      /* Rotationserkennung: Probelauf 0/90/180/270 auf verkleinertem Bild */
      const small=afOcrSmall(cv,800);
      let bestDeg=0,bestConf=-1;
      for(const deg of[0,90,180,270]){
        if(afOcrCancel)break;
        afOcrStat(`${label} – Ausrichtung prüfen (${deg}°) …`);
        try{
          const r=await afOcrWorker.recognize(afOcrRot(small,deg));
          if(r.data.confidence>bestConf){bestConf=r.data.confidence;bestDeg=deg;}
        }catch(e){if(afOcrCancel)break;throw e;}
      }
      if(afOcrCancel)break;
      afOcrStat(`${label} – Texterkennung (${bestDeg}° gedreht) …`);afOcrSetBar(0);
      const res=await afOcrWorker.recognize(afOcrRot(cv,bestDeg));
      await afOcrWorker.terminate();afOcrWorker=null;
      (res.data.lines||[]).forEach(l=>{afOcrConf[afLineKey(l.text)]=l.confidence;});
      const text=res.data.text||"";
      afOcrRawAll+=(afOcrRawAll?"\n":"")+`--- ${label} (Drehung ${bestDeg}°, Konfidenz ${Math.round(res.data.confidence)}%) ---\n`+text;
      const ta=document.getElementById("afTa");
      ta.value=(ta.value?ta.value+"\n":"")+text;
      afOcrHeads(text);
      afAnalyze();
      document.getElementById("afOcrRawBtn").style.display="";
      document.getElementById("afOcrRaw").textContent=afOcrRawAll;
      afToast(`${label}: Text erkannt (Gesamt-Konfidenz ${Math.round(res.data.confidence)}%) – bitte Vorschau prüfen.`);
    }
    if(afOcrCancel)afToast("OCR abgebrochen.");
  }catch(err){
    if(location.protocol==="file:")
      afToast("⚠️ OCR ist über file:// nicht möglich – bitte die Seite über einen lokalen Server oder gehostet öffnen.");
    else afToast("⚠️ OCR fehlgeschlagen: "+(err&&err.message||err));
  }finally{
    if(afOcrWorker){try{await afOcrWorker.terminate();}catch(e){}afOcrWorker=null;}
    delete document.getElementById("afFdatum").dataset.ocrOpen;
    afOcrBusy=false;
    prog.style.display="none";
  }
}
document.getElementById("afOcrPick").onclick=()=>document.getElementById("afOcrFile").click();
document.getElementById("afOcrFile").addEventListener("change",ev=>{
  const fs=[...ev.target.files];ev.target.value="";
  if(fs.length)afOcrRun(fs);
});
document.getElementById("afOcrCancel").onclick=async()=>{
  afOcrCancel=true;
  if(afOcrWorker){try{await afOcrWorker.terminate();}catch(e){}afOcrWorker=null;}
};
document.getElementById("afOcrRawBtn").onclick=()=>{
  const p=document.getElementById("afOcrRaw");
  const show=p.style.display!=="block";
  p.style.display=show?"block":"none";
  document.getElementById("afOcrRawBtn").textContent=show?"Rohtext ausblenden":"Rohtext anzeigen";
};
{
  const z=document.getElementById("afOcrZone");
  z.addEventListener("dragover",ev=>{ev.preventDefault();z.classList.add("drag");});
  z.addEventListener("dragleave",()=>z.classList.remove("drag"));
  z.addEventListener("drop",ev=>{
    ev.preventDefault();z.classList.remove("drag");
    const fs=[...ev.dataTransfer.files].filter(f=>/^image\//.test(f.type));
    if(fs.length)afOcrRun(fs);else afToast("Bitte Bilddatei(en) ablegen.");
  });
}

/* ---------- Overlays schließen ---------- */
document.querySelectorAll("[data-close]").forEach(b=>{
  b.onclick=()=>{document.getElementById(b.dataset.close).classList.remove("open");document.body.style.overflow="";};
});
document.querySelectorAll(".af-overlay").forEach(ov=>{
  ov.addEventListener("click",ev=>{if(ev.target===ov){ov.classList.remove("open");document.body.style.overflow="";}});
});
document.addEventListener("keydown",ev=>{
  if(ev.key!=="Escape")return;
  document.querySelectorAll(".af-overlay.open").forEach(ov=>{ov.classList.remove("open");document.body.style.overflow="";});
});

if(!afStoreOk)afToast("⚠️ localStorage nicht verfügbar – Aufträge können nicht dauerhaft gespeichert werden.");
render();
"""

def main():
    with open(os.path.join(PROJ, "index.html"), encoding="utf-8") as f:
        html = f.read()

    def splice(old, new):
        nonlocal html
        assert html.count(old) == 1, f"Anker nicht eindeutig: {old[:60]!r} ({html.count(old)}x)"
        html = html.replace(old, new)

    splice("<title>Mustertafeln-Katalog · engers</title>",
           "<title>Mustertafeln · Aufträge · engers</title>")
    splice("</style>", CSS + "\n</style>")
    splice("<body>\n<header>", "<body>\n" + BAR + "\n<header>")
    splice('<main><div id="grid">', "<main>" + BANNER + '<div id="grid">')
    splice('<div id="overlay">', DIALOGS + '\n<div id="overlay">')
    splice("render();\n</script>", "render();\n" + JS + "\n</script>")
    # Kennzeichnung im Kopf der Seite
    splice('<div class="brand">engers <small>·</small> Mustertafeln</div>',
           '<div class="brand">engers <small>·</small> Mustertafeln <small>· Aufträge</small></div>')

    with open(os.path.join(PROJ, "auftraege.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("auftraege.html geschrieben:", len(html), "Zeichen")

if __name__ == "__main__":
    main()
