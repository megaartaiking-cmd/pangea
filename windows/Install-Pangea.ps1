# Pangea 1.0 — Windows installer
# Installs Pangea to %LOCALAPPDATA%\Pangea, adds it to PATH,
# creates shortcuts, and links .pangea files to the interpreter.

$ErrorActionPreference = "Stop"
$InstallDir = Join-Path $env:LOCALAPPDATA "Pangea"
$SourceDir = Split-Path -Parent $PSScriptRoot

Write-Host "Installing Pangea 1.0 ..." -ForegroundColor Cyan

# 1. Python check — Pangea runs on Python 3.
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) {
    Write-Host ""
    Write-Host "Python 3 was not found on this PC." -ForegroundColor Yellow
    Write-Host "Pangea needs Python 3. Opening the download page ..."
    Start-Process "https://www.python.org/downloads/"
    Write-Host "Install Python 3 (tick 'Add python.exe to PATH' during setup), then run Install.bat again."
    pause
    exit 1
}
Write-Host ("Found Python: " + (& python --version))

# 2. Copy the language, the guide, and the examples.
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item (Join-Path $SourceDir "pangea.py") $InstallDir -Force
Copy-Item (Join-Path $SourceDir "PANGEA.md") $InstallDir -Force
Copy-Item (Join-Path $SourceDir "README.md") $InstallDir -Force
Copy-Item (Join-Path $SourceDir "examples") (Join-Path $InstallDir "examples") -Recurse -Force
Copy-Item (Join-Path $PSScriptRoot "pangea.bat") $InstallDir -Force

# 3. Add the install folder to your PATH.
$regPath = "HKCU:\Environment"
$currentPath = (Get-ItemProperty -Path $regPath -Name Path -ErrorAction SilentlyContinue).Path
if (-not $currentPath) { $currentPath = "" }
if (($currentPath -split ";") -notcontains $InstallDir) {
    $newPath = ($currentPath.TrimEnd(";") + ";" + $InstallDir).TrimStart(";")
    Set-ItemProperty -Path $regPath -Name Path -Value $newPath
    Write-Host "Added $InstallDir to your PATH."
}

# 4. Start Menu and Desktop shortcuts.
$shell = New-Object -ComObject WScript.Shell
$startMenu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Pangea"
New-Item -ItemType Directory -Force -Path $startMenu | Out-Null
$sc = $shell.CreateShortcut((Join-Path $startMenu "Pangea REPL.lnk"))
$sc.TargetPath = "cmd.exe"
$sc.Arguments = "/k pangea"
$sc.WorkingDirectory = $InstallDir
$sc.Description = "Pangea 1.0 — one language for people, machines, and minds"
$sc.Save()
$sc2 = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath("Desktop")) "Pangea.lnk"))
$sc2.TargetPath = "cmd.exe"
$sc2.Arguments = "/k pangea"
$sc2.WorkingDirectory = $InstallDir
$sc2.Description = "Pangea 1.0 — one language for people, machines, and minds"
$sc2.Save()

# 5. Link .pangea files to the interpreter, so double-clicking one runs it.
$classes = "HKCU:\Software\Classes"
New-Item -Path "$classes\.pangea" -Force | Out-Null
Set-ItemProperty -Path "$classes\.pangea" -Name "(default)" -Value "PangeaFile"
New-Item -Path "$classes\PangeaFile" -Force | Out-Null
Set-ItemProperty -Path "$classes\PangeaFile" -Name "(default)" -Value "Pangea Program"
New-Item -Path "$classes\PangeaFile\shell\open\command" -Force | Out-Null
Set-ItemProperty -Path "$classes\PangeaFile\shell\open\command" -Name "(default)" -Value "`"$InstallDir\pangea.bat`" `"%1`""

# 6. Verify the install works.
Write-Host ""
Write-Host "Verifying the install..."
& python (Join-Path $InstallDir "pangea.py") --check (Join-Path $InstallDir "examples\hello.pangaea")
Write-Host ""
Write-Host "Pangea 1.0 is installed in $InstallDir" -ForegroundColor Green
Write-Host "  pangea hello.pangaea       run a program"
Write-Host "  pangea                     open the interactive REPL"
Write-Host "  pangea --check file        check a program without running it"
Write-Host "You may need to open a new Command Prompt window for the PATH change to take effect."
pause
