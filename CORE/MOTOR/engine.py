import os
import subprocess
import urllib.request
import zipfile
import sys
import socket

# Configurações de Caminhos
user_docs = os.path.join(os.path.expanduser('~'), "Documents")
work_dir = os.path.join(user_docs, "Wandi Studio", "Engine", "arduino")
avr_path = os.path.join(os.path.expanduser('~'), "AppData", "Local", "Arduino15", "packages", "arduino", "hardware", "avr")
exe_path = os.path.join(work_dir, "arduino-cli.exe")
config_file = os.path.join(work_dir, "arduino-cli.yaml")

def tem_internet():
    """Verifica conexão de forma rápida para decidir o modo de operação."""
    try:
        socket.setdefaulttimeout(3)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except:
        return False

def initialize_wandi_engine():
    """
    Motor Inteligente Wandi. 
    Usa tags [SISTEMA], [PROCESSO], [INSTALAÇÃO] e 'Sincronizando' 
    para que a IDE direcione tudo para os Toasts e ignore no Output.
    """
    
    # --- FASE 1: DIAGNÓSTICO INICIAL ---
    print("<br><font color='#569cd6'><b>[SISTEMA] Iniciando verificação inteligente...</b></font>", flush=True)
    
    online = tem_internet()
    if online:
        print("<font color='#6a9955'><b>[SISTEMA] Conexão detectada. Modo Online ativado.</b></font>", flush=True)
    else:
        print("<font color='#ce9178'><b>[SISTEMA] Sem internet. Operando em Modo de Contingência (Offline).</b></font>", flush=True)

    # --- FASE 2: INTEGRIDADE DO DIRETÓRIO ---
    if not os.path.exists(work_dir):
        print("<font color='#888888'>Sincronizando: Criando estrutura de pastas...</font>", flush=True)
        os.makedirs(work_dir, exist_ok=True)

    # --- FASE 3: MOTOR DE COMPILAÇÃO (arduino-cli) ---
    if not os.path.exists(exe_path):
        if not online:
            print("<br><font color='#f44747'><b>[SISTEMA] ERRO: Motor ausente e sem internet para download!</b></font>", flush=True)
            return
        
        print("<br><font color='#ce9178'><b>[INSTALAÇÃO] Motor não encontrado. Iniciando provisionamento...</b></font>", flush=True)
        print("<font color='#888888'>Sincronizando: Baixando arduino-cli_latest_Win64...</font>", flush=True)
        
        try:
            url = "https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Windows_64bit.zip"
            zip_p = os.path.join(work_dir, "cli.zip")
            urllib.request.urlretrieve(url, zip_p)
            print("<font color='#888888'>Sincronizando: Extraindo componentes do motor...</font>", flush=True)
            with zipfile.ZipFile(zip_p, 'r') as zip_ref:
                zip_ref.extractall(work_dir)
            os.remove(zip_p)
            print("<font color='#6a9955'><b>[INSTALAÇÃO] Motor instalado com sucesso.</b></font>", flush=True)
        except Exception as e:
            print(f"<font color='#f44747'><b>[SISTEMA] Falha crítica no download: {e}</b></font>", flush=True)
            return

    # --- FASE 4: CONFIGURAÇÃO DO AMBIENTE ---
    if not os.path.exists(config_file):
        print("<font color='#888888'>Sincronizando: Gerando arquivos de configuração base...</font>", flush=True)
        subprocess.run([exe_path, "config", "init", "--overwrite", "--config-file", config_file], 
                       capture_output=True, cwd=work_dir, shell=True)

    # --- FASE 5: NÚCLEO DE HARDWARE (AVR) ---
    if online:
        print("<br><font color='#4ec9b0'><b>[PROCESSO] Sincronizando banco de dados de placas...</b></font>", flush=True)
        # Comando de atualização silencioso para o processo
        subprocess.run([exe_path, "core", "update-index", "--config-file", config_file], 
                       capture_output=True, cwd=work_dir, shell=True)
        
        if not os.path.exists(avr_path):
            print("<br><font color='#ce9178'><b>[INSTALAÇÃO] Arquitetura AVR não detectada. Instalando...</b></font>", flush=True)
            print("<font color='#888888'>Sincronizando: Isso pode levar alguns minutos...</font>", flush=True)
            
            process = subprocess.Popen([exe_path, "core", "install", "arduino:avr", "--config-file", config_file],
                                       stdout=subprocess.PIPE, text=True, cwd=work_dir, shell=True)
            for line in process.stdout:
                if "Installing" in line:
                    print(f"<font color='#888888'>Sincronizando: {line.strip()}</font>", flush=True)
            process.wait()
        else:
            print("<font color='#888888'>Sincronizando: Verificando atualizações de hardware...</font>", flush=True)
    else:
        # Verificação inteligente em modo offline
        if os.path.exists(avr_path):
            print("<font color='#6a9955'><b>[SISTEMA] Hardware AVR validado em cache local.</b></font>", flush=True)
        else:
            print("<br><font color='#f44747'><b>[SISTEMA] ERRO: Arquitetura AVR necessária não está instalada!</b></font>", flush=True)
            return

    # --- FASE 6: VERIFICAÇÃO FINAL ---
    if os.path.exists(exe_path) and os.path.exists(avr_path):
        print("<br><font color='#6a9955'><b>✅ Motor Wandi preparado e validado com sucesso!</b></font><br>", flush=True)
    else:
        print("<br><font color='#ce9178'><b>[SISTEMA] Ambiente iniciado com dependências pendentes.</b></font>", flush=True)