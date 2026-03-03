@echo off
title Initialize Git Repository

echo ========================================================
echo          Smart Elderly Nutritionist - Git Setup
echo ========================================================

REM 1. Check if Git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git is NOT installed or not in your PATH.
    echo.
    echo Please install Git using one of the following methods:
    echo 1. Download from: https://git-scm.com/download/win
    echo 2. Run in PowerShell (Admin): winget install --id Git.Git -e --source winget
    echo.
    echo After installing, please restart this terminal and run this script again.
    echo.
    pause
    exit /b
)

echo [OK] Git is installed.

REM 2. Initialize Repository
if exist .git (
    echo [INFO] Git repository already initialized.
) else (
    echo [INFO] Initializing new Git repository...
    git init
)

REM 3. Configure User (if not set)
git config user.name >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Git user.name not set.
    set /p GIT_USER="Enter your Name (e.g. John Doe): "
    set /p GIT_EMAIL="Enter your Email (e.g. john@example.com): "
    git config --global user.name "%GIT_USER%"
    git config --global user.email "%GIT_EMAIL%"
)

REM 4. Add and Commit
echo [INFO] Adding files...
git add .

echo [INFO] Committing files...
git commit -m "Initial commit: Smart Elderly Nutritionist System V2.0"

echo.
echo ========================================================
echo Repository Successfully Initialized!
echo ========================================================
echo Next Steps to Push to GitHub:
echo 1. Create a new repository on GitHub (https://github.com/new)
echo 2. Copy the repository URL (e.g., https://github.com/username/repo.git)
echo 3. Run the following commands in terminal:
echo    git remote add origin <your-repo-url>
echo    git branch -M main
echo    git push -u origin main
echo ========================================================
pause
