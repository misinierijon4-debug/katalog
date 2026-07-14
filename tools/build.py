import json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
data=json.loads((ROOT/"katalog.json").read_text(encoding="utf-8"))
key=next(k for k in data if "eintr" in k)
entries=data[key]
covers={}
c=ROOT/"tools"/"covers.json"
if c.exists(): covers=json.loads(c.read_text(encoding="utf-8"))
def slug(s): return re.sub(r"[^a-z0-9]+","-",(s or "").lower().translate(str.maketrans({"ä":"ae","ö":"oe","ü":"ue","ß":"ss"}))).strip("-")
out=[]
for e in entries:
 x=dict(e); x["img"]=(ROOT/"images"/"thumb"/(e["id"]+".jpg")).exists(); x.pop("board_px200",None)
 if slug(e.get("serie")) in covers: x["_covkey"]=slug(e.get("serie"))
 out.append(x)
(ROOT/"katalog.js").write_text("window.KATALOG_DATA = "+json.dumps(out,ensure_ascii=False,separators=(",",":"))+";\n",encoding="utf-8")
t=(ROOT/"index_template.html").read_text(encoding="utf-8")
t=t.replace("/*__COVERS__*/{}",json.dumps(covers,ensure_ascii=False,separators=(",",":")))
(ROOT/"index.html").write_text(t,encoding="utf-8")
print("built",len(out),"entries; engers",sum(e.get("marke")=="engers" for e in out),"vb",sum(e.get("marke")=="vb" for e in out))
