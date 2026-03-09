import subprocess
import threading
import serial
import serial.tools.list_ports
import os
from PyQt6.QtCore import QThread, pyqtSignal

def obter_portas_disponiveis() -> list[str]:
    return [porta.device for porta in serial.tools.list_ports.comports()]

class ArduinoCLI:
    def __init__(self, cli_path: str, fqbn: str = "arduino:avr:uno"):
        self.cli_path = cli_path
        self.fqbn = fqbn

    def _executar_comando(self, cmd: list[str], msg_inicio: str, msg_sucesso: str, msg_erro: str, callback_log):
        def tarefa():
            callback_log(f"\n[Wandi Engine] {msg_inicio}")
            
            if not os.path.exists(self.cli_path):
                callback_log(f"❌ ERRO: CLI não encontrado em: {self.cli_path}")
                return

            try:
                # Oculta a janela do console no Windows
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                processo = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    text=True,
                    startupinfo=startupinfo,
                    encoding='utf-8',
                    errors='replace'
                )
                
                stdout, stderr = processo.communicate()

                if processo.returncode == 0:
                    if stdout.strip(): callback_log(stdout)
                    callback_log(f"✔ SUCESSO: {msg_sucesso}")
                else:
                    if stderr.strip(): callback_log(stderr)
                    if stdout.strip(): callback_log(stdout)
                    callback_log(f"❌ {msg_erro}")
            except Exception as e:
                callback_log(f"❌ Erro fatal no subprocesso: {str(e)}")

        threading.Thread(target=tarefa, daemon=True).start()

    def compilar(self, sketch_path: str, callback_log):
        cmd = [self.cli_path, "compile", "--fqbn", self.fqbn, sketch_path]
        self._executar_comando(cmd, "Compilando...", "Código compilado!", "ERRO NA COMPILAÇÃO", callback_log)

    def upload(self, sketch_path: str, porta: str, callback_log):
        if not porta or porta == "Nenhuma porta":
            callback_log("❌ ERRO: Selecione uma porta serial.")
            return
        cmd = [self.cli_path, "upload", "-p", porta, "--fqbn", self.fqbn, sketch_path]
        self._executar_comando(cmd, f"Enviando para {porta}...", "Upload concluído!", "ERRO NO UPLOAD", callback_log)

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
                # Abre a conexão
                self.serial_conn = serial.Serial(self.porta, self.baudrate, timeout=0.1)
                
                # --- ADICIONE ESTA LINHA AQUI (LIMPEZA DE DADOS ANTIGOS) ---
                self.serial_conn.reset_input_buffer() 
                
                self.rodando = True
                self.conexao_status.emit(True)
                
                while self.rodando:
                    if self.serial_conn and self.serial_conn.is_open:
                        if self.serial_conn.in_waiting > 0:
                            # Usamos 'replace' em vez de 'ignore' para ver se há caracteres corrompidos
                            linha = self.serial_conn.readline().decode('utf-8', errors='replace').strip()
                            if linha: 
                                self.dados_recebidos.emit(linha)
                    self.msleep(5) # Reduzi para 5ms para maior fluidez no simulador
            except Exception as e:
                if self.rodando: self.erro_serial.emit(f"Erro Serial: {e}")
            finally:
                self.parar()

    def enviar(self, texto: str):
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write(f"{texto}\n".encode('utf-8'))
                self.dados_recebidos.emit(f"> {texto}") 
            except Exception as e:
                self.erro_serial.emit(f"Erro envio: {e}")

    def parar(self):
        self.rodando = False
        self.wait(200)
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.reset_input_buffer()
                self.serial_conn.close()
            except: pass
        self.serial_conn = None
        self.conexao_status.emit(False)