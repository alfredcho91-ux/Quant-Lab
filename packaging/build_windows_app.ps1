param(
    [string]$PythonBin = "",
    [string]$OutputDirectory = ""
)
$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $PSScriptRoot
if (-not $PythonBin) { $PythonBin = Join-Path $ProjectDir "backend\venv\Scripts\python.exe" }
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $ProjectDir "Windows" }
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
# Fresh output/work directories avoid deleting or replacing a running app.
$BuildRoot = Join-Path $ProjectDir (".cache\desktop-build-" + [guid]::NewGuid().ToString("N"))
$AppDirectory = Join-Path $OutputDirectory "Quant Lab"
$ArchivePath = Join-Path $OutputDirectory "Quant-Lab-Windows.zip"
if ((Test-Path -LiteralPath $AppDirectory) -or (Test-Path -LiteralPath $ArchivePath)) {
    throw "Output already exists. Choose a new -OutputDirectory; existing builds are preserved."
}
& $PythonBin -c "import PyInstaller, webview, pythonnet, clr_loader"
if ($LASTEXITCODE -ne 0) { throw "Install packaging\requirements-build.txt into the build Python first." }
Push-Location (Join-Path $ProjectDir "frontend")
try {
    npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed." }
} finally { Pop-Location }
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
Push-Location $ProjectDir
try {
    & $PythonBin -m PyInstaller --noconfirm --windowed --onedir --noupx `
        --name "Quant Lab" --distpath $OutputDirectory --workpath "$BuildRoot\work" --specpath $BuildRoot `
        --paths $ProjectDir --add-data "$ProjectDir\frontend\dist;frontend\dist" `
        --hidden-import ccxt.binance --hidden-import ccxt.binanceusdm `
        --hidden-import ccxt.bybit --hidden-import ccxt.okx --hidden-import keyring.backends.Windows `
        --hidden-import webview.platforms.winforms --hidden-import webview.platforms.edgechromium `
        --exclude-module pytest --exclude-module _pytest --exclude-module tkinter `
        --collect-all diskcache --collect-all cryptography --collect-all orjson --collect-all uvicorn `
        --collect-all webview --collect-all pythonnet --collect-all clr_loader `
        "$PSScriptRoot\desktop_entry.py"
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }
} finally { Pop-Location }
Copy-Item -LiteralPath (Join-Path $ProjectDir "docs\windows-desktop.md") -Destination $AppDirectory
Compress-Archive -LiteralPath $AppDirectory -DestinationPath $ArchivePath
Write-Host "Application: $AppDirectory\Quant Lab.exe"
Write-Host "Archive: $ArchivePath"
