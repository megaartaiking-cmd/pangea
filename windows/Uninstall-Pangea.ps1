# Pangea 1.0 — uninstaller. Removes the install folder, the PATH entry,
# the shortcuts, and the .pangea file link.

$ErrorActionPreference = "SilentlyContinue"
$InstallDir = Join-Path $env:LOCALAPPDATA "Pangea"

$regPath = "HKCU:\Environment"
$currentPath = (Get-ItemProperty -Path $regPath -Name Path -ErrorAction SilentlyContinue).Path
if ($currentPath) {
    $parts = $currentPath -split ";" | Where-Object { $_ -ne "" -and $_ -ne $InstallDir }
    Set-ItemProperty -Path $regPath -Name Path -Value ($parts -join ";")
}

Remove-Item (Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Pangea") -Recurse -Force
Remove-Item (Join-Path ([Environment]::GetFolderPath("Desktop")) "Pangea.lnk") -Force
Remove-Item "HKCU:\Software\Classes\.pangea" -Recurse -Force
Remove-Item "HKCU:\Software\Classes\PangeaFile" -Recurse -Force
Remove-Item $InstallDir -Recurse -Force

Write-Host "Pangea has been uninstalled."
pause
