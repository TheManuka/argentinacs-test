# ASCII-only script: all non-ASCII text lives in servers.tsv / card_template.html (UTF-8)
$scratch = $PSScriptRoot
$sitePath = Join-Path (Split-Path $PSScriptRoot -Parent) 'index.html'

$tsv = [System.IO.File]::ReadAllText((Join-Path $scratch 'servers.tsv'))
$card = [System.IO.File]::ReadAllText((Join-Path $scratch 'card_template.html'))

$sb = New-Object System.Text.StringBuilder
$openGrid = $false
$count = 0
foreach ($line in ($tsv -split "`n")) {
  $line = $line.TrimEnd("`r")
  if ($line -eq '') { continue }
  if ($line.StartsWith('#')) {
    if ($openGrid) { [void]$sb.Append("    </div>`n`n") }
    $title = $line.Substring(1)
    [void]$sb.Append('    <div class="divider-tag"><h3 class="text-gold">' + $title + '</h3></div>' + "`n")
    [void]$sb.Append('    <div class="server-grid">' + "`n")
    $openGrid = $true
  } else {
    $parts = $line -split "`t"
    $name = $parts[0]
    $ip = $parts[1]
    $nameUrl = [System.Uri]::EscapeDataString($name)
    [void]$sb.Append($card.Replace('{NAMEURL}', $nameUrl).Replace('{NAME}', $name).Replace('{IP}', $ip))
    $count++
  }
}
if ($openGrid) { [void]$sb.Append("    </div>`n") }
[void]$sb.Append("`n")
$block = $sb.ToString()

$html = [System.IO.File]::ReadAllText($sitePath)
$pat = '(?s)<div class="divider-tag">.*(?=<p class="server-note">)'
if (-not [regex]::IsMatch($html, $pat)) { Write-Output 'ERROR: patron no encontrado'; exit 1 }
$newHtml = [regex]::Replace($html, $pat, ($block.TrimStart() + '    '), 1)
[System.IO.File]::WriteAllText($sitePath, $newHtml, (New-Object System.Text.UTF8Encoding($false)))

$cards = ([regex]::Matches($newHtml, 'server-card cs')).Count
$groups = ([regex]::Matches($newHtml, 'divider-tag')).Count
Write-Output "OK: $count servidores en TSV; $cards cards en HTML; $groups grupos"
