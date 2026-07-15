# Rendert Seiten-HTMLs -> pages/seite-NNN.pdf und Board-HTMLs -> thumb/large JPG.
# Aufruf: powershell -File render_batch.ps1 -WorkDir <..> -RepoDir <..>
param([string]$WorkDir, [string]$RepoDir, [switch]$PdfOnly)
$ErrorActionPreference = "Continue"   # Edge schreibt Fortschritt auf stderr -> nicht als Fehler werten
Add-Type -AssemblyName System.Drawing
$edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if (-not (Test-Path $edge)) { $edge = "C:\Program Files\Microsoft\Edge\Application\msedge.exe" }
function FileUrl($p){ "file:///" + ($p -replace '\\','/') }
# Direkter Aufruf (beendet sauber, schnell); eigenes user-data-dir vermeidet Kollision mit offenem Edge
$udd = Join-Path $WorkDir '_edgeprofile'
function RunEdge([string[]]$eargs){
  & $edge ("--user-data-dir=$udd") @eargs 2>$null | Out-Null
}

# 1) Seiten -> PDF
$pageHtmls = Get-ChildItem (Join-Path $WorkDir 'pages') -Filter 'seite-*.html'
foreach($h in $pageHtmls){
  $seite = [regex]::Match($h.Name,'seite-(\d+)').Groups[1].Value
  $out = Join-Path $RepoDir "pages\seite-$seite.pdf"
  RunEdge @("--headless","--disable-gpu","--no-first-run","--no-pdf-header-footer","--print-to-pdf=$out",(FileUrl $h.FullName))
  Start-Sleep -Milliseconds 300
}
Write-Host "PDFs: $($pageHtmls.Count)"
if($PdfOnly){ Write-Host "PdfOnly - Thumbnails uebersprungen"; return }

# 2) Boards -> PNG -> thumb/large JPG (auf Board zugeschnitten)
$jpeg = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq "image/jpeg" }
$ep = New-Object System.Drawing.Imaging.EncoderParameters(1)
$ep.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, [long]90)

function CropToContent([System.Drawing.Bitmap]$bmp){
  $w=$bmp.Width; $h=$bmp.Height
  $data=$bmp.LockBits((New-Object System.Drawing.Rectangle(0,0,$w,$h)), [System.Drawing.Imaging.ImageLockMode]::ReadOnly, [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
  $stride=$data.Stride; $bytes=New-Object byte[] ($stride*$h)
  [System.Runtime.InteropServices.Marshal]::Copy($data.Scan0,$bytes,0,$bytes.Length); $bmp.UnlockBits($data)
  $minX=$w; $minY=$h; $maxX=0; $maxY=0
  for($yy=0;$yy -lt $h;$yy+=2){ $row=$yy*$stride; for($xx=0;$xx -lt $w;$xx+=2){ $o=$row+$xx*3; $bl=$bytes[$o]; $gr=$bytes[$o+1]; $rd=$bytes[$o+2]; if(-not($rd -gt 244 -and $gr -gt 244 -and $bl -gt 244)){ if($xx -lt $minX){$minX=$xx}; if($xx -gt $maxX){$maxX=$xx}; if($yy -lt $minY){$minY=$yy}; if($yy -gt $maxY){$maxY=$yy} } } }
  if($maxX -le $minX -or $maxY -le $minY){ return $bmp }
  $pad=3; $minX=[math]::Max(0,$minX-$pad); $minY=[math]::Max(0,$minY-$pad); $maxX=[math]::Min($w-1,$maxX+$pad); $maxY=[math]::Min($h-1,$maxY+$pad)
  $rect=New-Object System.Drawing.Rectangle($minX,$minY,($maxX-$minX),($maxY-$minY))
  $crop=New-Object System.Drawing.Bitmap($rect.Width,$rect.Height)
  $g=[System.Drawing.Graphics]::FromImage($crop); $g.DrawImage($bmp,(New-Object System.Drawing.Rectangle(0,0,$rect.Width,$rect.Height)),$rect,[System.Drawing.GraphicsUnit]::Pixel); $g.Dispose()
  return $crop
}

$boardHtmls = Get-ChildItem (Join-Path $WorkDir 'boards') -Filter '*.html'
$tmpPng = Join-Path $WorkDir '_shot.png'
foreach($h in $boardHtmls){
  $id = $h.BaseName
  if(Test-Path $tmpPng){ Remove-Item $tmpPng -Force }
  RunEdge @("--headless","--disable-gpu","--no-first-run","--hide-scrollbars","--window-size=560,860","--screenshot=$tmpPng",(FileUrl $h.FullName))
  Start-Sleep -Milliseconds 300
  if(-not (Test-Path $tmpPng)){ Write-Host "FEHLT: $id"; continue }
  $raw = New-Object System.Drawing.Bitmap($tmpPng)
  $src = CropToContent $raw
  $src.Save((Join-Path $RepoDir "images\large\$id.jpg"), $jpeg, $ep)
  $tw = 280; $th = [int]($src.Height * $tw / $src.Width)
  $thumb = New-Object System.Drawing.Bitmap($tw,$th)
  $g = [System.Drawing.Graphics]::FromImage($thumb); $g.InterpolationMode = "HighQualityBicubic"; $g.DrawImage($src,0,0,$tw,$th); $g.Dispose()
  $thumb.Save((Join-Path $RepoDir "images\thumb\$id.jpg"), $jpeg, $ep)
  $thumb.Dispose(); if($src -ne $raw){ $src.Dispose() }; $raw.Dispose(); Remove-Item $tmpPng -Force
}
Write-Host "Thumbnails: $($boardHtmls.Count)"
