# Erzeugt pro Tafel eine Board-SVG (fuer Thumbnail) und pro Seite eine A4-HTML
# im Engers-Katalogformat (fuer PDF-Druck). Liest boards.json + entries.json.
param(
  [string]$WorkDir,   # enthaelt boards.json + entries.json
  [string]$Serie      # Anzeigename der Serie fuer Kopfzeile (z.B. "CENTRO")
)
$ErrorActionPreference = "Stop"
$boards  = Get-Content (Join-Path $WorkDir 'boards.json')  -Encoding UTF8 | ConvertFrom-Json
$entries = Get-Content (Join-Path $WorkDir 'entries.json') -Encoding UTF8 | ConvertFrom-Json
$boardDir = Join-Path $WorkDir 'boards'; New-Item -ItemType Directory -Force $boardDir | Out-Null
$pageDir  = Join-Path $WorkDir 'pages';  New-Item -ItemType Directory -Force $pageDir  | Out-Null

function ParseWH($fmt) {
  $m = [regex]::Match($fmt, '([\d,\.]+)\s*x\s*([\d,\.]+)')
  $w = [double]($m.Groups[1].Value -replace ',','.')
  $h = [double]($m.Groups[2].Value -replace ',','.')
  return @($w,$h)
}
function Esc($s){ (($s -replace '&','&amp;') -replace '<','&lt;') -replace '>','&gt;' }

# Board-SVG: proportional zum Format, Fliesen als 30cm-Kurse in echten Farben,
# NEO-Foto-Tafeln mit Foto-Band oben.
function BoardSvg($b, [switch]$Standalone) {
  $wh = ParseWH $b.format; $W = $wh[0]; $H = $wh[1]
  $S = 4.0
  $pw = [math]::Round($W*$S,1); $ph = [math]::Round($H*$S,1)
  $mar = 6.0   # 1,5 cm Rahmen
  $fx = $mar; $fy = $mar; $fw = $pw - 2*$mar; $fh = $ph - 2*$mar
  $sb = New-Object System.Text.StringBuilder
  [void]$sb.Append("<svg viewBox='0 0 $pw $ph' xmlns='http://www.w3.org/2000/svg' preserveAspectRatio='xMidYMid meet'>")
  [void]$sb.Append("<rect x='0' y='0' width='$pw' height='$ph' fill='#4d4d4d'/>")
  # gewichtete Farbliste aus Fliesen (ohne Kombibord/Foto-Spezialbehandlung)
  $courseH = 30.0*$S
  $courses = [math]::Max(1,[math]::Floor($fh/$courseH))
  $cols = [math]::Max(1,[math]::Round($fw/(60.0*$S)))
  $fotoCourses = 0
  if($b.foto){ $fotoCourses = [math]::Min(2,[math]::Max(1,[math]::Floor($courses/3))) }
  $tileRows = $courses - $fotoCourses
  $cells = $tileRows * $cols
  # distinkte Farben + Zielanteile (gewichtet nach Stück), faire Verteilung (Bresenham)
  $distinct = @(); $weights = @()
  foreach($t in $b.tiles){ $idx = $distinct.IndexOf($t.color); if($idx -lt 0){ $distinct += $t.color; $weights += [double]([math]::Max(0.5,$t.stk)) } else { $weights[$idx] += [double]([math]::Max(0.5,$t.stk)) } }
  if($distinct.Count -eq 0){ $distinct=@('#d0cabb'); $weights=@(1.0) }
  $wsum = ($weights | Measure-Object -Sum).Sum
  $targets = @(); foreach($w in $weights){ $targets += ($w/$wsum*$cells) }
  $used = @(0)*$distinct.Count
  # Kurse zeichnen
  $y = $fy; $cellW = $fw/$cols
  for($c=0; $c -lt $courses; $c++){
    $ch = if($c -eq $courses-1){ $fy+$fh-$y } else { $courseH }
    if($c -lt $fotoCourses){
      [void]$sb.Append("<rect x='$fx' y='$([math]::Round($y,1))' width='$fw' height='$([math]::Round($ch,1))' fill='#333'/>")
      if($c -eq 0){ [void]$sb.Append("<text x='$([math]::Round($fx+$fw/2,1))' y='$([math]::Round($y+$ch/2+4,1))' fill='#bbb' font-family='Arial' font-size='11' text-anchor='middle'>Foto</text>") }
    } else {
      for($col=0; $col -lt $cols; $col++){
        # Farbe mit groesstem Rest (target-used) waehlen
        $best=0; $bestv=-9; for($i=0;$i -lt $distinct.Count;$i++){ $v=$targets[$i]-$used[$i]; if($v -gt $bestv){ $bestv=$v; $best=$i } }
        $used[$best]++; $cx = $fx + $col*$cellW
        [void]$sb.Append("<rect x='$([math]::Round($cx,1))' y='$([math]::Round($y,1))' width='$([math]::Round($cellW,1))' height='$([math]::Round($ch,1))' fill='$($distinct[$best])'/>")
      }
    }
    $y += $ch
  }
  # Fugenraster
  for($col=1; $col -lt $cols; $col++){ $gx=$fx+$col*$cellW; [void]$sb.Append("<line x1='$([math]::Round($gx,1))' y1='$([math]::Round($fy+$fotoCourses*$courseH,1))' x2='$([math]::Round($gx,1))' y2='$([math]::Round($fy+$fh,1))' stroke='#00000022' stroke-width='0.6'/>") }
  $gy = $fy + $courseH
  while($gy -lt $fy+$fh-1){ [void]$sb.Append("<line x1='$fx' y1='$([math]::Round($gy,1))' x2='$([math]::Round($fx+$fw,1))' y2='$([math]::Round($gy,1))' stroke='#00000022' stroke-width='0.6'/>"); $gy += $courseH }
  [void]$sb.Append("</svg>")
  $svg = $sb.ToString()
  if($Standalone){
    return "<!DOCTYPE html><html><head><meta charset='UTF-8'><style>body{margin:0;background:#fff;display:flex;justify-content:center;align-items:flex-start}svg{display:block;width:${pw}px;height:${ph}px}</style></head><body>$svg</body></html>"
  }
  return $svg
}

# --- Board-HTMLs (Screenshots) ---
foreach($b in $boards){
  [System.IO.File]::WriteAllText((Join-Path $boardDir "$($b.id).html"), (BoardSvg $b -Standalone), (New-Object System.Text.UTF8Encoding($false)))
}

# --- Seiten-HTMLs (PDF) ---
$css = @'
@page{size:A4 portrait;margin:0}*{box-sizing:border-box}
body{font-family:Arial,Helvetica,sans-serif;margin:0}
.page{width:210mm;min-height:297mm;padding:14mm 16mm;position:relative}
.logo{font-family:Georgia,"Times New Roman",serif;font-size:34pt;color:#1a1a1a}
.serie{position:absolute;top:22mm;right:16mm;text-align:right}
.serie .name{font-size:17pt;color:#9b9b9b}.serie .sub{font-size:8.5pt;color:#9b9b9b;margin-top:1mm}
.boards{display:flex;gap:14mm;margin-top:22mm;align-items:flex-start}
.tafel{width:80mm}.tafel .bx{width:100%;height:150mm;display:flex;align-items:flex-start;justify-content:center}
.tafel .bx svg{max-width:100%;max-height:150mm}
.caption{margin-top:5mm;font-size:8.5pt;color:#111;line-height:1.5}
.caption .nr{font-weight:bold;font-size:9pt}
.caption table{border-collapse:collapse;margin-top:2.5mm}.caption td{padding:0 2.5mm 0 0;font-size:8.5pt;white-space:nowrap}
.caption .lab{font-weight:bold;margin-top:2.5mm}
.hinweis{position:absolute;bottom:9mm;left:16mm;right:16mm;font-size:7pt;color:#999}
'@
$bySeite = $entries | Group-Object seite
foreach($grp in $bySeite){
  $seite = [int]$grp.Name
  $sb = New-Object System.Text.StringBuilder
  [void]$sb.Append("<!DOCTYPE html><html lang='de'><head><meta charset='UTF-8'><style>$css</style></head><body><div class='page'>")
  $serieName = if($Serie){ $Serie } else { ($grp.Group.serie | Select-Object -Unique -First 1) }
  $sub = ($grp.Group | Select-Object -First 1).material
  [void]$sb.Append("<div class='logo'>engers</div><div class='serie'><div class='name'>Serie $serieName</div><div class='sub'>$(Esc $sub)</div></div>")
  [void]$sb.Append("<div class='boards'>")
  foreach($e in $grp.Group){
    $b = $boards | Where-Object id -eq $e.id | Select-Object -First 1
    [void]$sb.Append("<div class='tafel'><div class='bx'>$(BoardSvg $b)</div><div class='caption'>")
    [void]$sb.Append("<div class='nr'>$($e.codes[0])</div><div>$(Esc $e.tafel_groesse)</div><table>")
    foreach($a in $e.artikel){ [void]$sb.Append("<tr><td>Art. $(Esc $a.artnr)</td><td>($($a.stueck) St.)</td><td>$(Esc $a.farbe)</td><td>$(Esc $a.groesse)</td></tr>") }
    [void]$sb.Append("</table>")
    if($e.label){ [void]$sb.Append("<div class='lab'>$(Esc $e.label)</div>") }
    $tp = ($e.notizen | Where-Object { $_ -match 'Tr.gerplatte' }) -replace '^Tr.gerplatte ',''
    if($tp){ [void]$sb.Append("<div class='lab'>Trägerplatte $(Esc $tp)</div>") }
    if($e.notizen -match 'Ambientebild'){ [void]$sb.Append("<div>+ Ambientebild/Foto</div>") }
    [void]$sb.Append("</div></div>")
  }
  [void]$sb.Append("</div>")
  [void]$sb.Append("<div class='hinweis'>Schematische Anordnung nach St&uuml;ckliste (ENGERS SampleBoard) &mdash; kein Original-Engers-Plan vorhanden. Farbkurse = Fliesenfarben, keine exakte Verlegung.</div>")
  [void]$sb.Append("</div></body></html>")
  [System.IO.File]::WriteAllText((Join-Path $pageDir "seite-$seite.html"), $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
}
Write-Host "Boards: $($boards.Count), Seiten-HTMLs: $($bySeite.Count)"
