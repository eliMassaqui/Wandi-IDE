import subprocess
import threading
import serial
import serial.tools.list_ports
from PyQt6.QtCore import QThread, pyqtSignal

# =======================================================
# 1. DETECÇÃO DE PORTAS
# =======================================================
def obter_portas_disponiveis() -> list[str]:
    """Retorna lista de strings com os nomes das portas COM disponíveis."""
    return [porta.device for porta in serial.tools.list_ports.comports()]


# =======================================================
# 2. COMPILAÇÃO E UPLOAD (ARDUINO CLI)
# =======================================================
class ArduinoCLI:
    def __init__(self, cli_path: str, fqbn: str = "arduino:avr:uno"):
        self.cli_path = cli_path
        self.fqbn = fqbn

    def _executar_comando(self, cmd: list[str], msg_inicio: str, msg_sucesso: str, msg_erro: str, callback_log):
        """Método auxiliar interno para evitar repetição de código (DRY) na criação de threads e subprocessos."""
        def tarefa():
            callback_log(f"--- [Wandi Engine] {msg_inicio} ---")
            try:
                processo = subprocess.run(cmd, capture_output=True, text=True)
                if processo.returncode == 0:
                    callback_log(f"✔ SUCESSO: {msg_sucesso}")
                    if processo.stdout.strip(): callback_log(processo.stdout)
                else:
                    callback_log(f"❌ {msg_erro}")
                    if processo.stderr.strip(): callback_log(processo.stderr)
            except Exception as e:
                callback_log(f"Erro inesperado no processo: {e}")

        threading.Thread(target=tarefa, daemon=True).start()

    def compilar(self, sketch_path: str, callback_log):
        cmd = [self.cli_path, "compile", "--fqbn", self.fqbn, sketch_path]
        self._executar_comando(
            cmd, "Iniciando Compilação", "Código compilado!", "ERRO NA COMPILAÇÃO:", callback_log
        )

    def upload(self, sketch_path: str, porta: str, callback_log):
        if not porta or porta == "Nenhuma porta":
            callback_log("❌ ERRO: Nenhuma porta selecionada para o upload.")
            return

        cmd = [self.cli_path, "upload", "-p", porta, "--fqbn", self.fqbn, sketch_path]
        self._executar_comando(
            cmd, f"Iniciando Upload na porta {porta}", f"Upload concluído na {porta}!", "ERRO NO UPLOAD:", callback_log
        )


# =======================================================
# 3. COMUNICAÇÃO SERIAL (ASSÍNCRONA)
# =======================================================
class MonitorSerial(QThread):
    dados_recebidos = pyqtSignal(str)
    erro_serial = pyqtSignal(str)
    conexao_status = pyqtSignal(bool) 

    def __init__(self, porta: str, baudrate: int = 9600):
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
            self.dados_recebidos.emit(f"--- Conectado a {self.porta} ({self.baudrate} baud) ---\n")
            
            while self.rodando and self.serial_conn.is_open:
                if self.serial_conn.in_waiting > 0:
                    linha = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                    if linha:
                        self.dados_recebidos.emit(linha)
        except Exception as e:
            self.erro_serial.emit(f"Erro na porta serial: {e}")
        finally:
            self.parar()

    def enviar(self, texto: str):
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write(f"{texto}\n".encode('utf-8'))
                self.dados_recebidos.emit(f"> {texto}") 
            except Exception as e:
                self.erro_serial.emit(f"Erro ao enviar: {e}")

    def parar(self):
        self.rodando = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.conexao_status.emit(False)
            self.dados_recebidos.emit(f"--- Desconectado de {self.porta} ---\n")