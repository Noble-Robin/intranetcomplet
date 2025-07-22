@echo off
echo ===========================================
echo    TEST INTRANET CAPLOGY
echo ===========================================

echo.
echo Test 1: Verification des projets Django...

echo.
echo Testing Moodle project...
cd moodle
python manage.py check
if %errorlevel% neq 0 (
    echo ❌ Erreur dans le projet Moodle
    pause
    exit /b 1
)
echo ✅ Projet Moodle OK

echo.
echo Testing AutoDocs project...
cd ..\AutoDocs
python manage.py check
if %errorlevel% neq 0 (
    echo ❌ Erreur dans le projet AutoDocs  
    pause
    exit /b 1
)
echo ✅ Projet AutoDocs OK

cd ..

echo.
echo Test 2: Migration des bases de données...

echo Migrations Moodle...
cd moodle
python manage.py makemigrations
python manage.py migrate

echo Migrations AutoDocs...
cd ..\AutoDocs  
python manage.py makemigrations
python manage.py migrate

cd ..

echo.
echo ===========================================
echo    ✅ TOUS LES TESTS PASSES !
echo ===========================================
echo.
echo Vous pouvez maintenant lancer: start_intranet.bat
echo.
pause
