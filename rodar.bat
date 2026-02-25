@echo off
setlocal enabledelayedexpansion

:: Cores ANSI
set "P=[95m" & :: Roxo (Wandi)
set "G=[92m" & :: Verde (Sucesso)
set "Y=[93m" & :: Amarelo (Ação)
set "B=[94m" & :: Azul (Info)
set "R=[91m" & :: Vermelho (Erro)
set "W=[0m"  & :: Reset

cls
echo %P%===========================================================%W%
echo %P%🚀        WANDI IDE - PREPARANDO O SEU AMBIENTE          %W%
echo %P%===========================================================%W%
echo.

:: --- ETAPA 1: PYTHON ---
echo %B%[ETAPA 1/3]%W% %Y%Instalando o motor: Python 3.13...%W%
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %B%[PROGRESSO]%W% [%G%####      %W%] 40%% - Extraindo arquivos...
    start /wait "" "ATRACAR\python-3.13.12-amd64.exe" /quiet InstallAllUsers=1 PrependPath=1
    echo %B%[PROGRESSO]%W% [%G%##########%W%] 100%% - Python configurado!
    echo %G%[OK] Python integrado ao sistema.%W%
) else (
    echo %G%[OK] Python ja detectado. Pulando instalacao...%W%
)

echo.
:: --- ETAPA 2: GIT ---
echo %B%[ETAPA 2/3]%W% %Y%Instalando o navegador de versoes: Git...%W%
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %B%[PROGRESSO]%W% [%G%##        %W%] 20%% - Iniciando setup silencioso...
    start /wait "" "ATRACAR\Git-2.53.0-64-bit.exe" /VERYSILENT /NORESTART
    echo %B%[PROGRESSO]%W% [%G%##########%W%] 100%% - Git configurado!
    echo %G%[OK] Git pronto para uso.%W%
) else (
    echo %G%[OK] Git ja esta presente no sistema.%W%
)

echo.
:: --- ETAPA 3: BIBLIOTECAS (Onde o progresso é real) ---
echo %B%[ETAPA 3/3]%W% %Y%Sincronizando bibliotecas da Wandi IDE...%W%
echo %B%[INFO]%W% Isso depende da sua internet e velocidade do disco.

echo %Y%-> Atualizando Pip...%W%
python -m pip install --upgrade pip --quiet

echo %Y%-> Instalando PySerial (Comunicacao USB)...%W%
python -m pip install pyserial --quiet
echo %B%[PROGRESSO]%W% [%G%###       %W%] 30%%

echo %Y%-> Instalando PyQt6 (Interface Grafica)...%W%
python -m pip install pyqt6 pyqt6-webengine --quiet
echo %B%[PROGRESSO]%W% [%G%#######    %W%] 70%%

echo %Y%-> Instalando PyInstaller (Gerador de Executaveis)...%W%
python -m pip install pyinstaller --quiet
echo %B%[PROGRESSO]%W% [%G%##########%W%] 100%%

echo.
echo %G%🎉 TUDO PRONTO! O AMBIENTE ESTA LÚCIDO E OPERACIONAL.%W%
echo %P%-----------------------------------------------------------%W%
echo %P%           iniciando main.py...                           %W%
echo %P%-----------------------------------------------------------%W%
echo.

python main.py

if %errorlevel% neq 0 (
    echo.
    echo %R%[!] Oops! A Wandi IDE fechou com um erro inesperado.%W%
    pause
)