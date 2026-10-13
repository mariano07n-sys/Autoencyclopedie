@echo off
echo.
echo  ============================================
echo   🚗 AutoEncyclopedie - Lancement complet
echo  ============================================
echo.

:: Démarrer l'API Python en arrière-plan
echo [1/2] Démarrage de l'API Python sur http://localhost:8000...
start "API AutoEncyclopedie" cmd /k "cd /d "%~dp0agent" && python api.py"
timeout /t 2 /nobreak >nul

:: Démarrer le site Next.js
echo [2/2] Démarrage du site web sur http://localhost:3000...
start "Site AutoEncyclopedie" cmd /k "cd /d "%~dp0web" && npm run dev"

echo.
echo  ✅ Tout est lancé !
echo  → Site web :  http://localhost:3000
echo  → API :       http://localhost:8000
echo.
pause
