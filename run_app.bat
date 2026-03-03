@echo off
title Smart Elderly Nutritionist System

echo ========================================================
echo        Smart Elderly Nutritionist - System Start
echo ========================================================

REM 1. Check for .env file
if not exist .env (
    echo [WARNING] .env file not found!
    echo Creating .env from .env.example...
    copy .env.example .env
    echo [IMPORTANT] Please edit .env file to set your DEEPSEEK_API_KEY before using!
    echo.
    pause
)

REM 2. Create necessary directories
if not exist logs mkdir logs
if not exist data mkdir data

echo [1/2] Starting Backend API (FastAPI)...
echo Backend will run on http://localhost:8002
start "Backend API - FastAPI" cmd /k "py -m uvicorn main:app --reload --port 8002"

echo Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

echo [2/2] Starting Frontend UI (Streamlit)...
echo Frontend will run on http://localhost:8501
start "Frontend UI - Streamlit" cmd /k "py -m streamlit run app.py --server.port 8501"

echo.
echo ========================================================
echo System is running!
echo --------------------------------------------------------
echo Backend Docs:  http://localhost:8000/docs
echo Frontend App:  http://localhost:8501
echo --------------------------------------------------------
echo To stop the system, close the opened terminal windows.
echo ========================================================
pause
