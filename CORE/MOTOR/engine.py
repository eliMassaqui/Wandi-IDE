import os
import subprocess
import urllib.request
import zipfile
import sys

# Lógica original de caminhos
user_docs = os.path.join(os.path.expanduser('~'), "Documents")
work_dir = os.path.join(user_docs, "Wandi Studio", "Engine", "arduino")
# Caminho para checagem do núcleo AVR
avr_path = os.path.join(os.path.expanduser('~'), "AppData", "Local", "Arduino15", "packages", "arduino", "hardware", "avr")

def initialize_wandi_engine():
    print("<br><font color='#569cd6'><b>[SISTEMA] Verificando ambiente de hardware para Sistemas Wandi...</b></font>", flush=True)
    
    if not os.path.exists(work_dir):
        os.makedirs(work_dir, exist_ok=True)
    
    exe_path = os.path.join(work_dir, "arduino-cli.exe")
    config_file = os.path.join(work_dir, "arduino-cli.yaml")

    # 1. Download do Binário
    if not os.path.exists(exe_path):
        print("<br><font color='#ce9178'><b>[INSTALAÇÃO] Provisionando motor Arduino CLI para Wandi Studio...</b></font>", flush=True)
        url = "https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Windows_64bit.zip"
        urllib.request.urlretrieve(url, os.path.join(work_dir, "cli.zip"))
        with zipfile.ZipFile(os.path.join(work_dir, "cli.zip"), 'r') as zip_ref:
            zip_ref.extractall(work_dir)
        os.remove(os.path.join(work_dir, "cli.zip"))

    def run_cli_clean(args, titulo):
        print(f"<br><font color='#4ec9b0'><b>[PROCESSO] {titulo}</b></font>", flush=True)
        cmd = [exe_path] + args + ["--config-file", config_file]
        
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
            text=True, cwd=work_dir, shell=True
        )

        # Filtro estilo Arduino IDE: mostra apenas milestones
        for line in process.stdout:
            l = line.strip()
            if any(key in l for key in ["Downloading", "Installing", "Configuring", "Installed", "Error"]):
                if "%" not in l and "KiB" not in l and "MiB" not in l:
                    print(f"<font color='#888888'>  > {l}</font>", flush=True)
        process.wait()

    # 2. Configuração Básica
    if not os.path.exists(config_file):
        run_cli_clean(["config", "init", "--overwrite"], "Inicializando arquivos de sistema...")

    # 3. Sincronização e Instalação/Upgrade do Core AVR
    run_cli_clean(["core", "update-index"], "Sincronizando banco de dados de Instalação/Upgrade...")

    if not os.path.exists(avr_path):
        run_cli_direct_msg = "Instalando compiladores da arquitetura AVR..."
        run_cli_clean(["core", "install", "arduino:avr"], run_cli_direct_msg)
    else:
        run_cli_clean(["core", "upgrade", "arduino:avr"], "Verificando atualizações do núcleo e placas da arquitetura AVR...")

    print("<br><font color='#6a9955'><b>✅ Motor do sistema Wandi preprado com sucesso!</b></font><br>", flush=True)