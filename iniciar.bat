@echo off
title Verificador de Licencas - EUA
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python nao encontrado. Instale em https://www.python.org/downloads/
    echo e marque a opcao "Add Python to PATH" durante a instalacao.
    pause
    exit /b
)

if not exist ".deps_ok" (
    echo Instalando dependencias ^(so na primeira vez^)...
    pip install -r requirements.txt -q && echo ok > .deps_ok
)

echo.
echo Iniciando... o navegador vai abrir sozinho em http://localhost:8000
echo Para encerrar o app, feche esta janela.
echo.
python app.py
pause
