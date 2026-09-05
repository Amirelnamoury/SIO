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
    if errorlevel 1 (
        echo ERREUR : impossible de creer l'environnement Python.
        pause
        exit /b 1
    )
)

set "VENV_PYTHON=%CD%\.venv\Scripts\python.exe"

"%VENV_PYTHON%" -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERREUR : impossible d'installer les dependances Python.
    echo Verifiez la connexion et la strategie de securite Windows.
    pause
    exit /b 1
)

echo Mise a jour de la base de donnees...
"%VENV_PYTHON%" -m alembic upgrade head
if errorlevel 1 (
    echo.
    echo ERREUR : la mise a jour de la base de donnees a echoue.
    echo Le backend n'a pas ete demarre pour eviter un schema incompatible.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Backend Suite Artisan demarre :
echo  http://localhost:8000
echo.
echo  NE FERMEZ PAS cette fenetre tant que vous testez.
echo ============================================
echo.

"%VENV_PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000

pause
