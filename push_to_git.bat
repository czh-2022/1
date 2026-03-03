@echo off
title Push to GitHub - Smart Elderly Nutritionist

echo ========================================================
echo          Smart Elderly Nutritionist - Git Push
echo ========================================================

REM 1. Check for Git
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git is NOT installed.
    echo Please install Git first: https://git-scm.com/download/win
    echo After installing, restart this script.
    pause
    exit /b
)

REM 2. Initialize & Commit
if not exist .git (
    echo [INFO] Initializing repository...
    git init
    git add .
    git commit -m "Initial commit: Smart Elderly Nutritionist V2.0"
) else (
    echo [INFO] Repository already initialized.
    echo [INFO] Adding any new changes...
    git add .
    git commit -m "Update project files"
)

REM 3. Set Remote & Push
echo [INFO] Setting remote origin to: https://github.com/czh-2022/1.git
git remote remove origin >nul 2>&1
git remote add origin https://github.com/czh-2022/1.git

echo [INFO] Renaming branch to 'main'...
git branch -M main

echo [INFO] Pushing to GitHub...
echo (You may be asked to sign in to GitHub in a browser window)
git push -u origin main

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Push failed. 
    echo Possible reasons:
    echo 1. Network issues (VPN might be needed).
    echo 2. Authentication failed.
    echo 3. The remote repository is not empty (try 'git pull origin main' first).
) else (
    echo.
    echo [SUCCESS] Project successfully deployed to GitHub!
)

pause
