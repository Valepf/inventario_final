@echo off
REM Activar entorno virtual, instalar dependencias y ejecutar la app

REM Navegar al directorio del proyecto
cd /d %~dp0

REM Crear entorno virtual si no existe
if not exist .venv (
    echo Creando entorno virtual...
    python -m venv .venv
)

REM Activar entorno virtual
call .venv\Scripts\activate.bat

REM Instalar dependencias
echo Instalando dependencias desde requirements.txt...
pip install -r requirements.txt

REM Establecer variables de entorno
set FLASK_APP=main.py
set FLASK_ENV=development

REM Iniciar Flask en segundo plano
start cmd /k flask run

REM Esperar unos segundos para asegurar que el servidor esté levantado
timeout /t 5 >nul

REM Abrir login.html en el navegador
start http://localhost:5000

REM Abrir Visual Studio Code en el proyecto
code .
