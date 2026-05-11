@echo off
cd /d "%~dp0"

if not exist ".git" (
    git init
    git remote add origin https://github.com/tomo-account/00_sample_app.git
    git branch -M main
)

git add .

git diff --cached --quiet
if %errorlevel% == 0 (
    echo No changes to commit.
    pause
    exit /b 0
)

set /p MSG="Commit message: "
if "%MSG%"=="" set MSG=update

git commit -m "%MSG%"
git push -u origin main

if %errorlevel% == 0 (
    echo Push succeeded.
) else (
    echo Push failed.
)
pause
