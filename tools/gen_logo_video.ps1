Add-Type -AssemblyName System.Drawing

$W = 960; $H = 540
$FPS = 24; $DUR = 16
$TOTAL = $FPS * $DUR
$outDir = Join-Path $PSScriptRoot "frames_logo"
if (Test-Path $outDir) { Remove-Item $outDir -Recurse -Force -Confirm:$false }
New-Item -ItemType Directory $outDir | Out-Null

# geometria del logo (unidades de disenio, cuadrado sin rotar, centrado en 0,0)
$rects = @(
  @(-32, -32, 64, 8), @(-32, 24, 64, 8), @(-32, -32, 8, 64), @(24, -32, 8, 64),
  @(-21, -21, 31, 8), @(13, -21, 8, 31), @(-10, 13, 31, 8), @(-21, -10, 8, 31)
)
$cx = 480.0; $cy = 270.0; $esc = 4.2

# path del logo ya transformado a coordenadas de pantalla (para clip y dibujo)
function NuevoPathLogo {
  $path = New-Object System.Drawing.Drawing2D.GraphicsPath([System.Drawing.Drawing2D.FillMode]::Winding)
  foreach ($r in $rects) {
    $path.AddRectangle((New-Object System.Drawing.RectangleF([single]($r[0]), [single]($r[1]), [single]($r[2]), [single]($r[3]))))
  }
  $m = New-Object System.Drawing.Drawing2D.Matrix
  $m.Translate([single]$cx, [single]$cy)
  $m.Rotate(45)
  $m.Scale([single]$esc, [single]$esc)
  $path.Transform($m)
  return $path
}

# destellos: dos barridos por loop, cada uno dura 2.5s
function PosDestello([double]$t) {
  foreach ($inicio in @(2.0, 10.0)) {
    if ($t -ge $inicio -and $t -lt ($inicio + 2.5)) { return ($t - $inicio) / 2.5 }
  }
  return -1
}

$fondo = [System.Drawing.Color]::FromArgb(255, 6, 7, 11)

for ($i = 0; $i -lt $TOTAL; $i++) {
  $t = $i / [double]$FPS
  $bmp = New-Object System.Drawing.Bitmap($W, $H)
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
  $g.Clear($fondo)

  # respiracion de brillo: 2 ciclos completos por loop (empalma perfecto)
  $puls = 0.86 + 0.14 * [math]::Sin(2 * [math]::PI * 2 * $t / $DUR - [math]::PI / 2)
  $g1 = [int]([math]::Min(255, 175 * $puls)); $g2 = [int](105 * $puls)
  $pTop = New-Object System.Drawing.PointF([single]$cx, [single]($cy - 200))
  $pBot = New-Object System.Drawing.PointF([single]$cx, [single]($cy + 200))
  $cTop = [System.Drawing.Color]::FromArgb(255, $g1, [int]([math]::Min(255, $g1 * 1.02)), [int]([math]::Min(255, $g1 * 1.08)))
  $cBot = [System.Drawing.Color]::FromArgb(255, $g2, [int]($g2 * 1.02), [int]([math]::Min(255, $g2 * 1.08)))
  $brocha = New-Object System.Drawing.Drawing2D.LinearGradientBrush($pTop, $pBot, $cTop, $cBot)

  $path = NuevoPathLogo
  $g.FillPath($brocha, $path)

  # destello: banda diagonal de luz que recorre el logo (recortada a su forma)
  $prog = PosDestello $t
  if ($prog -ge 0) {
    $g.SetClip($path)
    $u = 0.70710678
    $recorrido = 620.0
    $bx = ($cx - 310.0) + $recorrido * $prog
    $by = ($cy - 310.0 * 0.6) + $recorrido * 0.6 * $prog
    $ancho = 150.0
    $p1 = New-Object System.Drawing.PointF([single]($bx - $ancho * $u), [single]($by - $ancho * $u))
    $p2 = New-Object System.Drawing.PointF([single]($bx + $ancho * $u), [single]($by + $ancho * $u))
    $lgb = New-Object System.Drawing.Drawing2D.LinearGradientBrush($p1, $p2, [System.Drawing.Color]::FromArgb(0, 255, 255, 255), [System.Drawing.Color]::FromArgb(0, 255, 255, 255))
    $cb = New-Object System.Drawing.Drawing2D.ColorBlend(3)
    $cb.Colors = @([System.Drawing.Color]::FromArgb(0, 255, 255, 255), [System.Drawing.Color]::FromArgb(190, 255, 255, 255), [System.Drawing.Color]::FromArgb(0, 255, 255, 255))
    $cb.Positions = @([single]0, [single]0.5, [single]1)
    $lgb.InterpolationColors = $cb
    $g.FillRectangle($lgb, 0, 0, $W, $H)
    $g.ResetClip()
    $lgb.Dispose()
  }

  $g.Dispose(); $brocha.Dispose(); $path.Dispose()
  $bmp.Save((Join-Path $outDir ("f{0:D4}.png" -f $i)), [System.Drawing.Imaging.ImageFormat]::Png)
  $bmp.Dispose()
}
Write-Output "generados $TOTAL fotogramas en $outDir"
