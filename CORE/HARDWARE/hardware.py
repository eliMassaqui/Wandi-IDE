import subprocess
import threading
import serial
import serial.tools.list_ports
from PyQt6.QtCore import QThread, pyqtSignal

# =======================================================
# 1. DETECÇÃO DE PORTAS
# =======================================================
def obter_portas_disponiveis():
    """
    Retorna uma lista de strings com os nomes das portas COM disponíveis.
    Ex: ['COM3', 'COM5']
    """
    portas = serial.tools.list_ports.comports()
    return [porta.device for porta in portas]


# =======================================================
# 2. COMPILAÇÃO E UPLOAD (ARDUINO CLI)
# =======================================================
class ArduinoCLI:
    def __init__(self, cli_path, fqbn="arduino:avr:uno"):
        self.cli_path = cli_path
        self.fqbn = fqbn

    def compilar(self, sketch_path, callback_log):
        """
        Roda a compilação. callback_log é uma função para enviar os prints para a GUI.
        """
        def _tarefa_compilar():
            callback_log("--- [Wandi Engine] Iniciando Compilação ---")
            cmd = [self.cli_path, "compile", "--fqbn", self.fqbn, sketch_path]
            
            try:
                processo = subprocess.run(cmd, capture_output=True, text=True)
                if processo.returncode == 0:
                    callback_log("✔ SUCESSO: Código compilado!")
                    if processo.stdout.strip(): callback_log(processo.stdout)
                else:
                    callback_log("❌ ERRO NA COMPILAÇÃO:")
                    callback_log(processo.stderr)
            except Exception as e:
                callback_log(f"Erro ao tentar compilar: {e}")

        # Roda em thread para não travar a GUI
        threading.Thread(target=_tarefa_compilar, daemon=True).start()

    def upload(self, sketch_path, porta, callback_log):
        """
        Roda o upload para a placa conectada na porta especificada.
        """
        if not porta:
            callback_log("❌ ERRO: Nenhuma porta selecionada para o upload.")
            return

        def _tarefa_upload():
            callback_log(f"--- [Wandi Engine] Iniciando Upload na porta {porta} ---")
            cmd = [self.cli_path, "upload", "-p", porta, "--fqbn", self.fqbn, sketch_path]
            
            try:
                processo = subprocess.run(cmd, capture_output=True, text=True)
                if processo.returncode == 0:
                    callback_log(f"✔ SUCESSO: Upload concluído na {porta}!")
                    if processo.stdout.strip(): callback_log(processo.stdout)
                else:
                    callback_log("❌ ERRO NO UPLOAD:")
                    callback_log(processo.stderr)
            except Exception as e:
                callback_log(f"Erro ao tentar fazer upload: {e}")

        threading.Thread(target=_tarefa_upload, daemon=True).start()


# =======================================================
# 3. COMUNICAÇÃO SERIAL (ASSÍNCRONA)
# =======================================================
class MonitorSerial(QThread):
    """
    Usa QThread para ler a porta serial continuamente em segundo plano,
    emitindo sinais para atualizar a interface gráfica sem travamentos.
    """
    dados_recebidos = pyqtSignal(str)
    erro_serial = pyqtSignal(str)
    conexao_status = pyqtSignal(bool) # True = conectado, False = desconectado

    def __init__(self, porta, baudrate=9600):
        super().__init__()
        self.porta = porta
        self.baudrate = baudrate
        self.serial_conn = None
        self.rodando = False

    def run(self):
        try:
            self.serial_conn = serial.Serial(self.porta, self.baudrate, timeout=1)
            self.rodando = True
            self.conexao_status.emit(True)
            self.dados_recebidos.emit(f"--- Conectado a {self.porta} a {self.baudrate} baud ---\n")
            
            while self.rodando and self.serial_conn.is_open:
                if self.serial_conn.in_waiting > 0:
                    # Lê a linha, decodifica ignorando erros de caracteres estranhos
                    linha = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                    if linha:
                        self.dados_recebidos.emit(linha)
        except Exception as e:
            self.erro_serial.emit(f"Erro na porta serial: {str(e)}")
        finally:
            self.parar()

    def enviar(self, texto):
        """Envia um comando de texto para a placa Arduino"""
        if self.serial_conn and self.serial_conn.is_open:
            try:
                # Adiciona quebra de linha (padrão Arduino Serial.readStringUntil('\n'))
                comando = f"{texto}\n".encode('utf-8')
                self.serial_conn.write(comando)
                self.dados_recebidos.emit(f"> {texto}") # Ecoa na tela o que foi enviado
            except Exception as e:
                self.erro_serial.emit(f"Erro ao enviar: {str(e)}")

    def parar(self):
        """Encerra a conexão serial de forma limpa"""
        self.rodando = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.conexao_status.emit(False)
            self.dados_recebidos.emit(f"--- Desconectado de {self.porta} ---\n")