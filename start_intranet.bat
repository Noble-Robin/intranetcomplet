@echo off
echo ===========================================
echo    DEMARRAGE INTRANET CAPLOGY
echo ===========================================

echo.
echo Installation des dependances...
pip install -r requirements.txt

echo.
echo ===========================================
echo Demarrage du projet Moodle sur le port 8000...
start "Moodle Django" cmd /k "cd moodle && python manage.py runserver 8000"

echo.
echo Demarrage du projet AutoDocs sur le port 8001...
start "AutoDocs Django" cmd /k "cd AutoDocs && python manage.py runserver 8001"

echo.
echo Demarrage de la page d'accueil sur le port 3000...
start "Page Accueil" cmd /k "python start_homepage.py"

echo.
echo ===========================================
echo    TOUS LES SERVICES SONT DEMARRES !
echo ===========================================
echo.
echo - Page d'accueil: http://localhost:3000
echo - Moodle Manager: http://localhost:8000  
echo - AutoDocs:       http://localhost:8001
echo.
echo Appuyez sur une touche pour quitter...
pause >nul
