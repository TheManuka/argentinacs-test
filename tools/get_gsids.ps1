# Obtiene el GSID (id interno de GameTracker) de cada servidor del TSV
# y genera assets/gt_ids.js con el mapa { "ip:puerto": gsid }
$root = Split-Path $PSScriptRoot -Parent
$tsv = [System.IO.File]::ReadAllText((Join-Path $PSScriptRoot 'servers.tsv'))
$pares = @()
foreach ($line in ($tsv -split "`n")) {
  $line = $line.TrimEnd("`r")
  if ($line -eq '' -or $line.StartsWith('#')) { continue }
  $parts = $line -split "`t"
  $ip = $parts[1]
  try {
    $r = Invoke-WebRequest -Uri "https://www.gametracker.com/server_info/$ip/" -UseBasicParsing -TimeoutSec 25 -Headers @{ 'User-Agent' = 'Mozilla/5.0' }
    $m = [regex]::Match($r.Content, 'GSID=(\d+)')
    if ($m.Success) {
      $pares += "  `"$ip`": $($m.Groups[1].Value)"
      Write-Output "OK $($parts[0]) ($ip) -> GSID $($m.Groups[1].Value)"
    } else {
      Write-Output "SIN GSID: $($parts[0]) ($ip)"
    }
  } catch {
    Write-Output "ERROR $($parts[0]) ($ip): $($_.Exception.Message)"
  }
  Start-Sleep -Milliseconds 900
}
$js = "// Generado por tools/get_gsids.ps1 - id interno de GameTracker por servidor`nvar GT_IDS = {`n" + ($pares -join ",`n") + "`n};`n"
[System.IO.File]::WriteAllText((Join-Path $root 'assets\gt_ids.js'), $js, (New-Object System.Text.UTF8Encoding($false)))
Write-Output "Escrito assets/gt_ids.js con $($pares.Count) servidores"
