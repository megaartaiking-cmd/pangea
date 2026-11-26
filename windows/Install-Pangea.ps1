# Pangea 1.2 — Windows installer
# Python is bundled with Pangea, so nothing else needs to be installed.
# Installs to %LOCALAPPDATA%\Pangea, adds it to PATH, creates shortcuts,
# and links .pangea files to the interpreter.

$ErrorActionPreference = "Stop"
$InstallDir = Join-Path $env:LOCALAPPDATA "Pangea"
$SourceDir = Split-Path -Parent $PSScriptRoot

Write-Host "Installing Pangea 1.2 ..." -ForegroundColor Cyan

# 1. Check the bundled Python runtimes are here.
if (-not (Test-Path (Join-Path $SourceDir "python32\python.exe")) -or
    -not (Test-Path (Join-Path $SourceDir "python64\python.exe"))) {
    Write-Host "The install package is incomplete: the bundled Python folders (python32, python64) are missing." -ForegroundColor Red
    Write-Host "Please download Pangea 1.2 again and unzip the whole package before running Install.bat."
    pause
    exit 1
}

# 2. Copy the language, the bundled Python, the guide, and the examples.
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item (Join-Path $SourceDir "pangea.py") $InstallDir -Force
Copy-Item (Join-Path $SourceDir "PANGEA.md") $InstallDir -Force
Copy-Item (Join-Path $SourceDir "README.md") $InstallDir -Force
Copy-Item (Join-Path $SourceDir "examples") (Join-Path $InstallDir "examples") -Recurse -Force
Copy-Item (Join-Path $SourceDir "python32") (Join-Path $InstallDir "python32") -Recurse -Force
Copy-Item (Join-Path $SourceDir "python64") (Join-Path $InstallDir "python64") -Recurse -Force
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
$sc.Description = "Pangea 1.2 — one language for people, machines, and minds"
$sc.Save()
$sc2 = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath("Desktop")) "Pangea.lnk"))
$sc2.TargetPath = "cmd.exe"
$sc2.Arguments = "/k pangea"
$sc2.WorkingDirectory = $InstallDir
$sc2.Description = "Pangea 1.2 — one language for people, machines, and minds"
$sc2.Save()

# 5. Link .pangea files to the interpreter, so double-clicking one runs it.
$classes = "HKCU:\Software\Classes"
New-Item -Path "$classes\.pangea" -Force | Out-Null
Set-ItemProperty -Path "$classes\.pangea" -Name "(default)" -Value "PangeaFile"
New-Item -Path "$classes\PangeaFile" -Force | Out-Null
Set-ItemProperty -Path "$classes\PangeaFile" -Name "(default)" -Value "Pangea Program"
New-Item -Path "$classes\PangeaFile\shell\open\command" -Force | Out-Null
Set-ItemProperty -Path "$classes\PangeaFile\shell\open\command" -Name "(default)" -Value "`"$InstallDir\pangea.bat`" `"%1`""

# 6. Verify the install works, using the bundled Python.
$pyDir = if ($env:PROCESSOR_ARCHITECTURE -eq "x86") { "python32" } else { "python64" }
$py = Join-Path $InstallDir "$pyDir\python.exe"
Write-Host ""
Write-Host "Verifying the install..."
& $py (Join-Path $InstallDir "pangea.py") --check (Join-Path $InstallDir "examples\hello.pangaea")
Write-Host ""
Write-Host "Pangea 1.2 is installed in $InstallDir" -ForegroundColor Green
Write-Host "  pangea hello.pangaea       run a program"
Write-Host "  pangea                     open the interactive REPL"
Write-Host "  pangea --check file        check a program without running it"
Write-Host "You may need to open a new Command Prompt window for the PATH change to take effect."
pause
