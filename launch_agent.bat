@echo off
echo.
echo  ============================================
echo   🤖 Agent IA - Collecte des données
echo  ============================================
echo.
cd /d "%~dp0agent"

echo  Choisissez une action :
echo  1. Collecter toutes les marques
echo  2. Collecter tous les modèles
echo  3. Collecte complète (marques + modèles)
echo  4. Menu interactif
echo  5. Afficher les statistiques
echo.
set /p choice="Votre choix (1-5) : "

if "%choice%"=="1" python main.py --collect-brands
if "%choice%"=="2" python main.py --collect-models
if "%choice%"=="3" python main.py --full-run
if "%choice%"=="4" python main.py
if "%choice%"=="5" python main.py --stats

echo.
pause
