@echo off
chcp 65001 >nul
echo ========================================================
echo Starting PDFMathTranslate (DeepSeek Enhanced Edition)...
echo ========================================================
echo.
set GRADIO_SERVER_PORT=27860
set NO_PROXY=localhost,127.0.0.1,0.0.0.0
set no_proxy=localhost,127.0.0.1,0.0.0.0

python app.py
pause
