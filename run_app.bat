@echo off
setlocal
title Running Streamlit App
echo Dang kiem tra moi truong Python...

:: Kiem tra thu muc venv (Dung dau ngoac kep de tranh loi duong dan)
if not exist "venv\" (
    echo Dang khoi tao moi truong ao (venv)...
    python -m venv venv
)

:: Kich hoat venv
echo Dang kich hoat venv...
set "VENV_PATH=%~dp0venv\Scripts\activate.bat"
if exist "%VENV_PATH%" (
    call "%VENV_PATH%"
) else (
    echo Khong tim thay venv. Vui long kiem tra lai!
    pause
    exit /b
)

:: Cai dat thu vien va chay app
echo Dang kiem tra thu vien...
pip install -r requirements.txt
echo Dang khoi chay ung dung...
streamlit run app.py

pause