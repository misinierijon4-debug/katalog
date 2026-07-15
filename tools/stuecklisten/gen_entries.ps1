# Generiert Katalog-Einträge + Board-SVGs aus einer BOM-JSON (Stücklisten-Export).
# Aufruf: powershell -File gen_entries.ps1 -BomJson <pfad> -StartSeite 312 -OutDir <pfad>
param(
  [string]$BomJson,
  [int]$StartSeite = 312,
  [string]$OutDir,
  [string]$SerieName   # optional: erzwingt Serienname fuer alle (z.B. "COLOR IT")
)
$ErrorActionPreference = "Stop"
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Force $OutDir | Out-Null }
$bom = Get-Content $BomJson -Encoding UTF8 | ConvertFrom-Json

# --- Farbzuordnung nach Stichwort in der Fliesenbeschreibung ---
function TileColor($desc) {
  $d = $desc.ToUpper()
  # COLOR IT / EO Farben zuerst (spezifisch)
  if ($d -match 'KIESELWEIß|KIESELWEISS')   { return '#ece7dd' }
  if ($d -match 'ATOLLGRÜN|ATOLLGRUEN')     { return '#3f8f7f' }
  if ($d -match 'SIENABRAUN')               { return '#8a5a3c' }
  if ($d -match 'KIRSCHROT')                { return '#9e2b2b' }
  if ($d -match 'FJORDBLAU')                { return '#2f5f8a' }
  if ($d -match 'SILBERGRAU')               { return '#b9bcbf' }
  if ($d -match 'TINTENSCHWARZ')            { return '#2a2a2e' }
  if ($d -match 'MANDELBRAUN')              { return '#7a5540' }
  if ($d -match 'WELLENDEKOR')              { return '#e3e3df' }
  if ($d -match 'WEIß-GLÄNZEND|WEISS-GLÄNZEND|WEIß-MATT|WEISS-MATT') { return '#ececec' }
  # NEO / CENTRO / NATURAL
  if ($d -match 'WEIß-BEIGE|WEISS-BEIGE') { return '#e8e0d2' }
  if ($d -match 'WEIß-GRAU|WEISS-GRAU')   { return '#dcdde0' }
  if ($d -match 'NATURBEIGE')             { return '#d8cbb0' }
  if ($d -match 'TABAKBRAUN')             { return '#7a6047' }
  if ($d -match 'ANTIKGRAU')              { return '#9a9a98' }
  if ($d -match 'GRAPHIT')                { return '#54555a' }
  if ($d -match 'ZEMENT')                 { return '#b1ada5' }
  if ($d -match 'SCHOKO')                 { return '#6b5544' }
  if ($d -match 'SAND')                   { return '#d8c8a6' }
  if ($d -match 'GRAU')                   { return '#c2c3c5' }
  if ($d -match 'BEIGE')                  { return '#ded2bd' }
  if ($d -match 'WEIß|WEISS')             { return '#ececec' }
  return '#d0cabb'
}
# --- Artikelnummer aus Materialcode (z.B. 1CEN-1220-0T-10 -> CEN 1220) ---
function ArtNr($art) {
  if ($art -match '^\d?([A-Z]{2,4})-?(\d{3,4})') { return ($Matches[1] + ' ' + $Matches[2]) }
  return $art
}
# --- Farbe/Finish aus Beschreibung: Serie+Größe weg, R-Werte und Codes weg ---
function TileFarbe($desc) {
  # alles bis inkl. erster Größenangabe (z.B. "COLOR IT 20X20CM ", "EO 40X120X0,6 ") entfernen
  $rest = [regex]::Replace($desc, '^.*?[\d,]+X[\d,]+(?:X[\d,]+)?\s*(?:CM)?\s*', '')
  # R-Wert + Zusatzkuerzel (auch angehaengt wie MANDELBRAUNR10BDP), UK/KD/DP/REKT. entfernen
  $rest = $rest -replace 'R\d{1,2}B?(?:DP)?','' -replace '\bUK\b','' -replace '\bKD\b','' -replace 'REKT\.?','' -replace '\bDP\b','' -replace '\s+',' '
  return $rest.Trim().Trim('.',' ').Trim().ToLower()
}
function TileGroesse($desc) {
  if ($desc -match '([\d,]+)X([\d,]+)') { return ($Matches[1] + 'x' + $Matches[2] + ' cm') }
  return '30x60 cm'
}
function IdFromCode($code, $seite) { return ('p{0}_{1}' -f $seite, ($code -replace '[^0-9A-Za-z]','')) }

# Format aus tafeldesc (MT/GT/MDT <format>CM ...)
function Format($tafeldesc) {
  $t = $tafeldesc.Trim()
  # Maß direkt nach MT/GT/MDT; CM optional (viele COLOR-IT-Beschreibungen ohne CM)
  if ($t -match '^(?:MDT|MT|GT)\s*([\d,]+[xX][\d,]+)') { return ($Matches[1] -replace 'X','x') }
  return '?'
}
function IsGT($tafeldesc) { return ($tafeldesc.Trim() -match '^GT') }

$codes = $bom | Select-Object -ExpandProperty code -Unique | Sort-Object { ($_ -split '-')[1] }, { $_ }
# Sortierung: erst Serie (NEPO/CTRO), dann Code – für saubere Seitenpaare
$codes = $bom.code | Sort-Object -Unique
$codesBySerie = $codes | Sort-Object @{e={($_ -split '-')[1]}}, @{e={$_}}

$entries = @()
$boards = @()   # für SVG-Rendering: @{id;serie;format;tiles=@(@{color;label;stk})}
foreach ($code in $codesBySerie) {
  $rows = $bom | Where-Object code -eq $code
  $first = $rows[0]
  $serieCode = ($code -split '-')[1]
  $serie = if ($SerieName) { $SerieName } elseif ($serieCode -eq 'NEPO') { 'NEO' } elseif ($serieCode -eq 'CTRO') { 'CENTRO' } else { $first.serie }
  $fmt = Format $first.tafeldesc
  $gt = IsGT $first.tafeldesc
  $tiles = $rows | Where-Object typ -eq 'Tiles'
  $board = $rows | Where-Object typ -eq 'Wooden Board' | Select-Object -First 1
  $poster = $rows | Where-Object typ -eq 'POSTER' | Select-Object -First 1
  $hasFoto = ($first.tafeldesc -match 'FOTO')

  $artikel = @()
  $svgTiles = @()
  $sizeCount = @{}
  foreach ($t in $tiles) {
    $g = (TileGroesse $t.artdesc)
    $artikel += [ordered]@{ artnr = (ArtNr $t.art); stueck = ($t.stueck -replace '\.0$',''); farbe = (TileFarbe $t.artdesc); groesse = $g }
    $svgTiles += @{ color = (TileColor $t.artdesc); stk = [double]($t.stueck -replace ',','.'); label = (ArtNr $t.art) }
    $sk = [double]($t.stueck -replace ',','.'); if(-not $sizeCount.ContainsKey($g)){ $sizeCount[$g]=0 }; $sizeCount[$g]+=$sk
  }
  # Material = haeufigste Fliesengroesse (nach Stück); Fallback 30x60
  $material = 'Steingut 30x60cm'
  if ($sizeCount.Count -gt 0) { $material = ($sizeCount.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 1).Key -replace ' cm','cm' }
  $label = if ($poster) { "Poster $($poster.art)" } else { '' }
  $notizen = @("aus ENGERS_SampleBoard-Stückliste ($($first.bom)), kein Original-Plan – schematische Klebevorlage 07/2026")
  if ($board) { $notizen += "Trägerplatte $($board.art) ($($board.artdesc.Trim()))" }
  if ($hasFoto) { $notizen += "Tafel enthält Ambientebild/Foto" }
  if ($code -match '!') { $notizen += "Hinweis: Original-Code enthält Sonderzeichen (Datenfehler in Stückliste)" }

  $seite = $StartSeite + [math]::Floor(($entries.Count) / 2)
  $id = IdFromCode $code $seite
  $entry = [ordered]@{
    id = $id; seite = $seite; serie = $serie; material = $material;
    codes = @($code); tafel_groesse = "$fmt cm"; gt = $gt; artikel = $artikel;
    label = $label; notizen = $notizen; display = $false; marke = 'engers'
  }
  $entries += $entry
  $boards += @{ id = $id; serie = $serie; format = $fmt; tiles = $svgTiles; foto = $hasFoto; code = $code }
}

$entries | ConvertTo-Json -Depth 6 | Out-File (Join-Path $OutDir 'entries.json') -Encoding utf8
$boards  | ConvertTo-Json -Depth 6 | Out-File (Join-Path $OutDir 'boards.json') -Encoding utf8
Write-Host "Einträge: $($entries.Count), Seiten: $($StartSeite)..$($StartSeite + [math]::Ceiling($entries.Count/2) - 1)"
