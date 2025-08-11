param(
  [Parameter(Mandatory=$true, Position=0)]
  [string]$InSvg,
  [string]$Inkscape = "C:\\Program Files\\Inkscape\\bin\\inkscape.com",
  [switch]$NoPreprocess,
  [Parameter(ValueFromRemainingArguments=$true)]
  [string[]]$PlotterArgs
)

$ErrorActionPreference = "Stop"
$InSvg = (Resolve-Path $InSvg).Path
$OutSvg = [IO.Path]::Combine((Split-Path $InSvg), ([IO.Path]::GetFileNameWithoutExtension($InSvg) + "_out.svg"))

if (-not $NoPreprocess) {
  & $Inkscape $InSvg --export-plain-svg="$OutSvg" --actions "select-all:all;object-to-path;stroke-to-path;export-do;file-close-all"
} else {
  $OutSvg = $InSvg
}

python -m silhouette.plotter_manager $OutSvg @PlotterArgs
