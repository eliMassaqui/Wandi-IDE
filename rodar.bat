@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: Cores ANSI
set "P=[95m" & set "G=[92m" & set "Y=[93m" & set "B=[94m" & set "R=[91m" & set "W=[0m"

cls
echo %P%===========================================================%W%
echo %P%🚀          WANDI IDE - PREPARANDO O SEU AMBIENTE          %W%
echo %P%===========================================================%W%

:: --- ETAPA 1: PYTHON ---
echo.
echo %B%[ETAPA 1/3]%W% %Y%Verificando Python 3.13...%W%
python --version >nul 2>&1
if %errorlevel% neq 0 (
    if exist "ATRACAR\python-3.13.12-amd64.exe" (
        echo %B%[PROGRESSO]%W% [%G%####      %W%] 40%% - Instalando...
        "ATRACAR\python-3.13.12-amd64.exe" /quiet InstallAllUsers=1 PrependPath=1
        echo %G%[OK] Python configurado!%W%
    ) else (
        echo %R%[AVISO] Instalador do Python não encontrado em ATRACAR\.%W%
    )
) else (
    echo %G%[OK] Python já detectado.%W%
)

:: --- ETAPA 2: GIT ---
echo.
echo %B%[ETAPA 2/3]%W% %Y%Verificando Git...%W%
git --version >nul 2>&1
if %errorlevel% neq 0 (
    if exist "ATRACAR\Git-2.53.0-64-bit.exe" (
        echo %B%[PROGRESSO]%W% [%G%##        %W%] 20%% - Iniciando setup...
        "ATRACAR\Git-2.53.0-64-bit.exe" /VERYSILENT /NORESTART
        echo %G%[OK] Git pronto para uso.%W%
    ) else (
        echo %R%[AVISO] Instalador do Git não encontrado em ATRACAR\.%W%
    )
) else (
    echo %G%[OK] Git já está presente.%W%

)

:: --- ETAPA 3: BIBLIOTECAS ---
echo.
echo %B%[ETAPA 3/3]%W% %Y%Sincronizando bibliotecas...%W%
python -m pip install --upgrade pip --quiet
python -m pip install pyserial pyqt6 pyqt6-webengine pyinstaller --quiet

echo.
echo %G%🎉 TUDO PRONTO! AMBIENTE LÚCIDO E OPERACIONAL.%W%
echo %P%-----------------------------------------------------------%W%
echo %P%            Iniciando main.py...                           %W%
echo %P%-----------------------------------------------------------%W%

python main.py

if %errorlevel% neq 0 (
    echo.
    echo %R%[!] Erro crítico ao iniciar o main.py.%W%
    pause
)