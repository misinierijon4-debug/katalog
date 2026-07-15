# Fuegt Eintraege aus entries.json in katalog.json (Format-erhaltend, Textsplice)
# und katalog.js (window.KATALOG_DATA, kompakt, img:true) ein.
# Aufruf: powershell -File insert_entries.ps1 -EntriesJson <..> -RepoDir <..>
param([string]$EntriesJson, [string]$RepoDir)
$ErrorActionPreference = "Stop"
$entries = Get-Content $EntriesJson -Encoding UTF8 | ConvertFrom-Json
$enc = New-Object System.Text.UTF8Encoding($false)

function J($s){ if($null -eq $s){return '""'}; '"' + (($s -replace '\\','\\') -replace '"','\"') + '"' }

# --- katalog.json: Eintrag im Handstil (Basis 2 Leerzeichen) ---
function EntryJson($e){
  $sb = New-Object System.Text.StringBuilder
  [void]$sb.Append("  {`n")
  [void]$sb.Append("   `"id`": $(J $e.id),`n")
  [void]$sb.Append("   `"seite`": $($e.seite),`n")
  [void]$sb.Append("   `"serie`": $(J $e.serie),`n")
  [void]$sb.Append("   `"material`": $(J $e.material),`n")
  [void]$sb.Append("   `"codes`": [`n")
  $cj = ($e.codes | ForEach-Object { "    $(J $_)" }) -join ",`n"
  [void]$sb.Append("$cj`n   ],`n")
  [void]$sb.Append("   `"tafel_groesse`": $(J $e.tafel_groesse),`n")
  $gtv = $e.gt.ToString().ToLower()
  [void]$sb.Append("   `"gt`": $gtv,`n")
  [void]$sb.Append("   `"artikel`": [`n")
  $aj = @()
  foreach($a in $e.artikel){
    $aj += "    {`n     `"artnr`": $(J $a.artnr),`n     `"stueck`": $(J $a.stueck),`n     `"farbe`": $(J $a.farbe),`n     `"groesse`": $(J $a.groesse)`n    }"
  }
  [void]$sb.Append(($aj -join ",`n"))
  [void]$sb.Append("`n   ],`n")
  [void]$sb.Append("   `"label`": $(J $e.label),`n")
  [void]$sb.Append("   `"notizen`": [`n")
  $nj = ($e.notizen | ForEach-Object { "    $(J $_)" }) -join ",`n"
  [void]$sb.Append("$nj`n   ],`n")
  [void]$sb.Append("   `"display`": false,`n")
  [void]$sb.Append("   `"marke`": $(J $e.marke)`n")
  [void]$sb.Append("  }")
  return $sb.ToString()
}

$jsonPath = Join-Path $RepoDir 'katalog.json'
$txt = [System.IO.File]::ReadAllText($jsonPath, [System.Text.Encoding]::UTF8)
# Einfuegemarke: Ende des eintraege-Arrays -> "\r?\n ],\r?\n \"probleme\"" (CRLF-tolerant)
$m = [regex]::Match($txt, "\r?\n \],\r?\n `"probleme`"")
if(-not $m.Success){ throw "Marker (Ende eintraege) nicht gefunden" }
$idx = $m.Index
$nl = if($txt.Contains("`r`n")){ "`r`n" } else { "`n" }
$block = (($entries | ForEach-Object { EntryJson $_ }) -join ",`n")
$block = ("," + "`n" + $block) -replace "`r?`n", $nl
$new = $txt.Substring(0,$idx) + $block + $txt.Substring($idx)
[System.IO.File]::WriteAllText($jsonPath, $new, $enc)
Write-Host "katalog.json: $($entries.Count) Eintraege eingefuegt"

# --- katalog.js: kompakt, img:true, vor abschliessendem ]; ---
function EntryJsCompact($e){
  $codes = '[' + (($e.codes | ForEach-Object { J $_ }) -join ',') + ']'
  $art = '[' + (($e.artikel | ForEach-Object { '{"artnr":' + (J $_.artnr) + ',"stueck":' + (J $_.stueck) + ',"farbe":' + (J $_.farbe) + ',"groesse":' + (J $_.groesse) + '}' }) -join ',') + ']'
  $notiz = '[' + (($e.notizen | ForEach-Object { J $_ }) -join ',') + ']'
  $gtv = $e.gt.ToString().ToLower()
  return '{"id":' + (J $e.id) + ',"seite":' + $e.seite + ',"serie":' + (J $e.serie) + ',"material":' + (J $e.material) + ',"codes":' + $codes + ',"tafel_groesse":' + (J $e.tafel_groesse) + ',"gt":' + $gtv + ',"artikel":' + $art + ',"label":' + (J $e.label) + ',"notizen":' + $notiz + ',"display":false,"marke":' + (J $e.marke) + ',"img":true}'
}
$jsPath = Join-Path $RepoDir 'katalog.js'
$js = [System.IO.File]::ReadAllText($jsPath, [System.Text.Encoding]::UTF8)
$blockJs = ($entries | ForEach-Object { EntryJsCompact $_ }) -join ','
$close = $js.LastIndexOf('}];')
if($close -lt 0){ throw "katalog.js Array-Ende nicht gefunden" }
$newJs = $js.Substring(0, $close+1) + ',' + $blockJs + $js.Substring($close+1)
[System.IO.File]::WriteAllText($jsPath, $newJs, $enc)
Write-Host "katalog.js: $($entries.Count) Eintraege eingefuegt"
