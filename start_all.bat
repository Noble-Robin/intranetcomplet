@echo off
echo ============================================
echo     DEMARRAGE INTRANET CAPLOGY
echo ============================================
echo.

echo 📚 Demarrage du projet Moodle (port 8000)...
start "Moodle Project" cmd /k "cd /d %~dp0moodle && python manage.py runserver 127.0.0.1:8000"

echo.
timeout /t 3 /nobreak >nul

echo 📄 Demarrage du projet AutoDocs (port 8001)...
start "AutoDocs Project" cmd /k "cd /d %~dp0AutoDocs && python manage.py runserver 127.0.0.1:8001"

echo.
timeout /t 3 /nobreak >nul

echo 🏠 Demarrage de la page d'accueil (port 3000)...
start "Homepage" cmd /k "cd /d %~dp0 && python start_homepage.py"

echo.
echo ✅ Tous les serveurs sont en cours de demarrage !
echo.
echo 📱 Ouvrez votre navigateur sur :
echo    🏠 Page d'accueil : http://localhost:3000
echo    📚 Moodle        : http://localhost:8000  
echo    📄 AutoDocs      : http://localhost:8001
echo.
pause
