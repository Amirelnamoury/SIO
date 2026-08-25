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

echo.
echo ============================================
echo  Tableau de bord Suite Artisan disponible :
echo  http://localhost:8080
echo.
echo  NE FERMEZ PAS cette fenetre tant que vous testez.
echo  (Le backend doit deja tourner dans une autre fenetre)
echo ============================================
echo.

python -m http.server 8080

pause
