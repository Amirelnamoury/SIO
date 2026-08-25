@echo off
cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ============================================
    echo ERREUR : Python n'est pas installe, ou pas
    echo ajoute au PATH pendant l'installation.
    echo Voir les instructions fournies pour l'installer.
    echo ============================================
    echo.
    pause
    exit /b 1
)

if not exist ".venv" (
    echo Premier lancement : installation en cours, patientez une minute...
    python -m venv .venv
)

call .venv\Scripts\activate.bat
pip install -q -r requirements.txt

echo.
echo ============================================
echo  Backend Suite Artisan demarre :
echo  http://localhost:8000
echo.
echo  NE FERMEZ PAS cette fenetre tant que vous testez.
echo ============================================
echo.

uvicorn app.main:app --host 127.0.0.1 --port 8000

pause
