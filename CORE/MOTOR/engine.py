import os
import subprocess
import urllib.request
import zipfile
import sys

# Configurações de Caminhos
user_docs = os.path.join(os.path.expanduser('~'), "Documents")
work_dir = os.path.join(user_docs, "Wandi Studio", "Engine", "arduino")
avr_path = os.path.join(os.path.expanduser('~'), "AppData", "Local", "Arduino15", "packages", "arduino", "hardware", "avr")
exe_path = os.path.join(work_dir, "arduino-cli.exe")
config_file = os.path.join(work_dir, "arduino-cli.yaml")

def tem_internet():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request('https://www.google.com', headers=headers)
        urllib.request.urlopen(req, timeout=4)
        return True
    except:
        return False

def initialize_wandi_engine():
    print("<br><font color='#569cd6'><b>[SISTEMA] Iniciando verificação inteligente...</b></font>", flush=True)
    
    online = tem_internet()
    if online:
        print("<font color='#6a9955'><b>[SISTEMA] Conexão detectada. Modo Online ativado.</b></font>", flush=True)
    else:
        print("<font color='#ce9178'><b>[SISTEMA] Sem internet. Operando em Modo de Contingência (Offline).</b></font>", flush=True)

    # 1. Estrutura
    os.makedirs(work_dir, exist_ok=True)

    # 2. Motor Binário
    if not os.path.exists(exe_path):
        if not online:
            print("<br><font color='#f44747'><b>[SISTEMA] ERRO: Motor ausente e sem internet!</b></font>", flush=True)
            return
        
        print("<br><font color='#ce9178'><b>[INSTALAÇÃO] Motor não encontrado. Provisionando...</b></font>", flush=True)
        try:
            url = "https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Windows_64bit.zip"
            zip_p = os.path.join(work_dir, "cli.zip")
            opener = urllib.request.build_opener()
            opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
            urllib.request.install_opener(opener)
            urllib.request.urlretrieve(url, zip_p)
            with zipfile.ZipFile(zip_p, 'r') as zip_ref:
                zip_ref.extractall(work_dir)
            os.remove(zip_p)
        except Exception as e:
            print(f"<font color='#f44747'><b>[SISTEMA] Falha no download: {e}</b></font>", flush=True)
            return

    # 3. Configuração (Sempre garante que o arquivo existe para as fases seguintes)
    if not os.path.exists(config_file):
        subprocess.run([exe_path, "config", "init", "--overwrite", "--config-file", config_file], 
                       capture_output=True, cwd=work_dir, shell=True)

    # 4. Sincronização e Instalação Progressiva de Hardware
    if online:
        print("<br><font color='#4ec9b0'><b>[PROCESSO] Sincronizando banco de dados de placas...</b></font>", flush=True)
        # Forçamos o update do index para evitar erro de pacote não encontrado
        subprocess.run([exe_path, "core", "update-index", "--config-file", config_file], 
                       capture_output=True, cwd=work_dir, shell=True)
        
        # Só instala se a pasta física NÃO existir
        if not os.path.exists(avr_path):
            print("<br><font color='#ce9178'><b>[INSTALAÇÃO] Arquitetura AVR não detectada. Instalando agora...</b></font>", flush=True)
            
            # Feedback progressivo para não parecer travado
            process = subprocess.Popen([exe_path, "core", "install", "arduino:avr", "--config-file", config_file],
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=work_dir, shell=True)
            
            for line in process.stdout:
                line_clean = line.strip()
                if line_clean:
                    print(f"<font color='#888888'>Sincronizando: {line_clean}</font>", flush=True)
            process.wait()

    # --- FASE 6: VERIFICAÇÃO FINAL LÚCIDA ---
    motor_ok = os.path.exists(exe_path)
    hardware_ok = os.path.exists(avr_path)

    if motor_ok and hardware_ok:
        print("<br><font color='#6a9955'><b>✅ Motor Wandi preparado e validado com sucesso!</b></font><br>", flush=True)
    else:
        print("<br><font color='#f44747'><b>[SISTEMA] Falha Crítica: O ambiente não pôde ser totalmente preparado.</b></font>", flush=True)
        if not hardware_ok:
            print("<font color='#888888'>Dica: Verifique se o antivírus não bloqueou a criação da pasta em AppData.</font>", flush=True)

if __name__ == "__main__":
    initialize_wandi_engine()