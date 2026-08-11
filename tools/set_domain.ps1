# Estampa el dominio real en todo el sitio (reemplaza https://TU-DOMINIO.com)
# Uso:  powershell -NoProfile -ExecutionPolicy Bypass -File tools/set_domain.ps1 -Domain "https://argentinacs.com"
param([Parameter(Mandatory = $true)][string]$Domain)

$Domain = $Domain.TrimEnd('/')
if ($Domain -notmatch '^https?://') { $Domain = 'https://' + $Domain }

$root = Split-Path $PSScriptRoot -Parent
$files = @('index.html', 'tienda.html', 'vip.html', 'robots.txt', 'sitemap.xml')
$placeholder = 'https://TU-DOMINIO.com'

foreach ($f in $files) {
  $p = Join-Path $root $f
  if (-not (Test-Path $p)) { Write-Output "SKIP $f (no existe)"; continue }
  $t = [System.IO.File]::ReadAllText($p)
  $n = ([regex]::Matches($t, [regex]::Escape($placeholder))).Count
  if ($n -eq 0) { Write-Output "OK $f (sin cambios)"; continue }
  $t = $t.Replace($placeholder, $Domain)
  [System.IO.File]::WriteAllText($p, $t, (New-Object System.Text.UTF8Encoding($false)))
  Write-Output "OK $f ($n reemplazos)"
}
Write-Output "Listo. Dominio estampado: $Domain"
