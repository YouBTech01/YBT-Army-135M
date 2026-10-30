@echo off
setlocal
title YBT Army
cd /d "%~dp0"

echo ==================================================
echo    YBT Army
echo ==================================================
echo.

REM ---------------------------------------------------------------
REM 1. Find Python 3.10 or newer (the Microsoft Store stub does not count)
REM ---------------------------------------------------------------
call :find_python
if defined YBT_TEST_NOPYTHON set "PY="
if defined PY goto have_python

echo [WARNING] Python 3.10 or newer was not found on this computer.
echo           YBT Army needs Python to run, so it must be installed first.
echo.
choice /c YN /n /m "Install Python 3.12 now? It is automatic and takes about a minute [Y/N]: "
if errorlevel 2 goto manual_python

call :install_python
if defined YBT_TEST_NOPYTHON goto end_test
call :find_python
if defined PY goto have_python

echo.
echo [ERROR] Python was installed but this window cannot see it yet.
echo         Close this window and double-click run_you_b_tech.bat again.
echo.
pause
exit /b 1

:manual_python
echo.
echo Install Python from https://www.python.org/downloads/
echo and tick "Add python.exe to PATH" during setup. Then run this file again.
start "" "https://www.python.org/downloads/"
echo.
pause
exit /b 1

:have_python
echo [1/3] Python ready.

REM ---------------------------------------------------------------
REM 2. Virtual environment (recreated if it is broken)
REM ---------------------------------------------------------------
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import sys" >nul 2>nul
    if errorlevel 1 rmdir /s /q ".venv"
)
if not exist ".venv\Scripts\python.exe" (
    echo [2/3] Creating virtual environment...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Could not create the virtual environment.
        pause
        exit /b 1
    )
)

REM ---------------------------------------------------------------
REM 3. Packages: only installed on the first run or when requirements.txt changes
REM ---------------------------------------------------------------
fc /b requirements.txt ".venv\requirements.installed" >nul 2>nul
if errorlevel 1 (
    echo [2/3] Installing packages. This takes a few minutes the first time...
    ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check --prefer-binary -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ERROR] Package installation failed. Check your internet connection and run this file again.
        pause
        exit /b 1
    )
    copy /y requirements.txt ".venv\requirements.installed" >nul
) else (
    echo [2/3] Packages ready.
)

REM ---------------------------------------------------------------
REM 4. Model check
REM ---------------------------------------------------------------
if not exist "YBT-Army-135M\model.safetensors" (
    echo.
    echo [ERROR] The YBT-Army-135M model folder was not found next to this file.
    pause
    exit /b 1
)
for %%F in ("YBT-Army-135M\model.safetensors") do if %%~zF LSS 1000000 (
    echo.
    echo [ERROR] model.safetensors is only a Git LFS placeholder, not the real weights.
    echo         Run:  git lfs install   then   git lfs pull
    pause
    exit /b 1
)

REM ---------------------------------------------------------------
REM 5. Start the web UI (Streamlit opens your browser by itself)
REM ---------------------------------------------------------------
if defined YBT_NO_LAUNCH goto end_test
echo [3/3] Starting YBT Army. Your browser opens in a moment. Press Ctrl+C here to stop.
echo.
".venv\Scripts\python.exe" -m streamlit run ybt_app.py
echo.
echo YBT Army has stopped.
pause
exit /b 0

:end_test
echo (test mode: stopped before launch)
exit /b 0

REM ===============================================================
:find_python
set "PY="
py -3 -c "import sys;sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul && set "PY=py -3"
if defined PY exit /b 0
python -c "import sys;sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul && set "PY=python"
if defined PY exit /b 0
for %%V in (313 312 311 310) do (
    if not defined PY if exist "%LocalAppData%\Programs\Python\Python%%V\python.exe" set PY="%LocalAppData%\Programs\Python\Python%%V\python.exe"
)
exit /b 0

:install_python
if defined YBT_TEST_NOPYTHON (
    echo test mode: skipping the real installation
    exit /b 0
)
echo.
where winget >nul 2>nul
if not errorlevel 1 (
    echo Installing Python 3.12 with winget...
    winget install -e --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements
    call :find_python
    if defined PY exit /b 0
)
echo Downloading the Python 3.12 installer from python.org...
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -UseBasicParsing 'https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe' -OutFile '%TEMP%\ybt-python-setup.exe' } catch { exit 1 }"
if errorlevel 1 (
    echo [ERROR] The download failed. Install Python manually from https://www.python.org/downloads/
    exit /b 1
)
echo Installing Python 3.12 (a few seconds)...
"%TEMP%\ybt-python-setup.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1 Include_test=0
del "%TEMP%\ybt-python-setup.exe" >nul 2>nul
exit /b 0
