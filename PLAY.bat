@echo off
title LLM CHESS 3D Launcher

:: Try to use 'py' first, fallback to 'python'
where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set PYTHON_CMD=py
    set PIP_CMD=py -m pip
) else (
    where python >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        set PYTHON_CMD=python
        set PIP_CMD=python -m pip
    ) else (
        echo [!] Python is not installed or not in your system PATH!
        pause
        exit /b
    )
)

echo ==============================================
echo   LLM CHESS 3D - Setup ^& Launch
echo ==============================================

echo [*] Checking dependencies...
%PYTHON_CMD% -c "import panda3d, chess, requests" 2>NUL
if errorlevel 1 (
    echo [*] Installing missing libraries - this happens only once...
    %PIP_CMD% install panda3d chess requests
) else (
    echo [+] All required libraries are ready!
)

echo.
echo [*] Launching the 3D Game...
%PYTHON_CMD% main.py