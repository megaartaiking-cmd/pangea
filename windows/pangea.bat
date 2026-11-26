@echo off
where python >nul 2>&1
if %errorlevel%==0 (
    python "%~dp0pangea.py" %*
) else (
    py -3 "%~dp0pangea.py" %*
)
