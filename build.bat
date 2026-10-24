@echo off
REM ===========================================================================
REM  Build the CSU Attendance kiosk into a distributable folder.
REM
REM  Role in the system: produces dist\CSU Attendance\, which runs on a machine
REM  that has never had Python installed. PLAN.md asks for this at least three
REM  weeks before the defense, because a packaged build behaves differently from
REM  `python main.py` and this is where projects lose days.
REM
REM  What it does that `pyinstaller` alone does not:
REM    * copies models\ BESIDE the .exe rather than inside it. PyInstaller would
REM      unpack 300 MB of ONNX into a temp directory on every launch, turning a
REM      two-second start into thirty. See csu_attendance.spec.
REM    * copies .env.example but never .env -- shipping the database and admin
REM      passwords inside a distributable would be an audit finding.
REM
REM  Usage:   build.bat
REM ===========================================================================

setlocal
cd /d "%~dp0"

set APP_NAME=CSU Attendance
set DIST_DIR=dist\%APP_NAME%
set PYTHON=.venv\Scripts\python.exe

echo.
echo === CSU Attendance -- build ===
echo.

if not exist "%PYTHON%" (
    echo ERROR: %PYTHON% not found.
    echo        Create the virtualenv first:  python -m venv .venv
    echo        then:  .venv\Scripts\pip install -r requirements.txt
    exit /b 1
)

if not exist "models\buffalo_l" (
    echo ERROR: models\buffalo_l is missing.
    echo        The model pack ships beside the executable, so it has to exist
    echo        here before the distribution folder can be assembled.
    exit /b 1
)

echo [1/4] Cleaning previous build...
if exist "build" rmdir /s /q "build"
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"

echo [2/4] Running PyInstaller (this takes several minutes)...
"%PYTHON%" -m PyInstaller csu_attendance.spec --noconfirm --clean
if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller failed. The output above says why.
    exit /b 1
)

echo [3/4] Copying the model pack beside the executable...
REM /E include subdirectories, /I assume a directory, /Q quiet, /Y overwrite.
REM /EXCLUDE skips buffalo_l.zip -- insightface leaves the downloaded archive
REM beside the folder it extracted, and shipping both doubles the distribution
REM for a file nothing ever reads again.
xcopy "models" "%DIST_DIR%\models" /E /I /Q /Y /EXCLUDE:build_exclude.txt >nul
if errorlevel 1 (
    echo ERROR: could not copy models\ into the distribution.
    exit /b 1
)

echo [4/4] Copying the configuration template and the scripts...
copy /Y ".env.example" "%DIST_DIR%\.env.example" >nul
if exist "PLAN.md" copy /Y "PLAN.md" "%DIST_DIR%\PLAN.md" >nul

REM init_db.py is needed on a fresh terminal, and it is a plain script rather
REM than part of the frozen application -- so the source and the interpreter it
REM needs are not in the distribution. Shipped for reference; run it from a
REM machine that has Python, against the same database.
if not exist "%DIST_DIR%\scripts" mkdir "%DIST_DIR%\scripts"
copy /Y "scripts\init_db.py" "%DIST_DIR%\scripts\init_db.py" >nul

echo.
echo === Build complete ===
echo.
echo   Folder : %CD%\%DIST_DIR%
echo   Run    : "%DIST_DIR%\%APP_NAME%.exe"
echo.
echo   Before handing this to anyone:
echo     1. Copy .env.example to .env in the distribution folder and edit
echo        DB_PASSWORD and ADMIN_PASSWORD. It is deliberately not shipped.
echo     2. Run scripts\init_db.py once against the target database.
echo     3. Launch it on a machine that has never had Python installed --
echo        that is the only test that proves the build.
echo.

endlocal
