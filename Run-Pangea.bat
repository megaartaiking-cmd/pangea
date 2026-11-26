@echo off
rem Pangea 1.2 — portable mode. No install needed.
rem Just double-click this file and Pangea opens, using the Python bundled with it.
title Pangea 1.2
if "%PROCESSOR_ARCHITECTURE%"=="x86" (
    set "PY=%~dp0python32\python.exe"
) else (
    set "PY=%~dp0python64\python.exe"
)
if exist "%PY%" (
    "%PY%" "%~dp0pangea.py"
) else (
    python "%~dp0pangea.py"
)
pause
