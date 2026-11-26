@echo off
rem Pangea launcher — uses the Python bundled with Pangea.
rem Picks the 32-bit or 64-bit runtime to match this PC.
set "PANGEA_HOME=%~dp0"
if "%PROCESSOR_ARCHITECTURE%"=="x86" (
    set "PY=%PANGEA_HOME%python32\python.exe"
) else (
    set "PY=%PANGEA_HOME%python64\python.exe"
)
if exist "%PY%" (
    "%PY%" "%PANGEA_HOME%pangea.py" %*
) else (
    python "%PANGEA_HOME%pangea.py" %*
)
