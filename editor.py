import sys
import os
import subprocess
import threading
from pathlib import Path

# UI Framework
from PyQt6.QtWidgets import (
    QMainWindow, QToolBar, QTabWidget, QPlainTextEdit, 
    QTextEdit, QDockWidget, QWidget, QVBoxLayout
)
from PyQt6.QtGui import QAction, QIcon, QFont
from PyQt6.QtCore import Qt, QSize

# Import do seu compilador personalizado
from compilador import compiladorWandi 

class WandiEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Configuração de Caminhos (Realista)
        self.base_path = os.path.join(Path.home(), "Documents", "Wandi Studio", "Engine")
        self.arduino_cli = os.path.join(self.base_path, "arduino", "arduino-cli.exe")
        self.wiring_folder = os.path.join(self.base_path, "WIRING")
        
        self.compilador = compiladorWandi()
        
        # Setup de UI
        self.setWindowTitle("Wandi Editor - Núcleo de Compilação")
        self.resize(1000, 700)
        self._init_ui()

    def _init_ui(self):
        # 1. Editor de Código
        self.tabs = QTabWidget()
        self.code_editor = QPlainTextEdit()
        self.code_editor.setFont(QFont("Consolas", 12))
        self.code_editor.setPlainText("def setup():\n    pinMode(13, OUTPUT)\n\ndef loop():\n    digitalWrite(13, 1)\n    delay(1000)")
        self.tabs.addTab(self.code_editor, "main.py")
        self.setCentralWidget(self.tabs)

        # 2. Console de Saída (Output)
        self.console_dock = QDockWidget("Mensageiro do Sistema", self)
        self.output_log = QTextEdit()
        self.output_log.setReadOnly(True)
        self.output_log.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; font-family: 'Consolas';")
        self.console_dock.setWidget(self.output_log)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.console_dock)

        # 3. Toolbar de Ações
        toolbar = QToolBar("Ações")
        toolbar.setIconSize(QSize(30, 30))
        self.addToolBar(toolbar)

        btn_compilar = QAction("Compilar", self)
        btn_compilar.triggered.connect(self.processar_compilacao)
        toolbar.addAction(btn_compilar)

    def log(self, mensagem, cor="#d4d4d4"):
        """Adiciona mensagens ao console da IDE"""
        self.output_log.append(f"<span style='color:{cor};'>{mensagem}</span>")
        self.output_log.ensureCursorVisible()

    def processar_compilacao(self):
        """Fluxo: Tradução -> Salvamento -> arduino-cli"""
        codigo_py = self.code_editor.toPlainText()
        
        self.log("--- Iniciando Processo Wandi ---")
        
        # TRADUÇÃO VIA AST
        self.log("Tradução: Python para Wiring...")
        codigo_cpp = self.compilador.translate(codigo_py)
        
        if "ERRO" in codigo_cpp:
            self.log(f"Tradução falhou: {codigo_cpp}", "red")
            return

        # SALVAMENTO EM DISCO
        os.makedirs(self.wiring_folder, exist_ok=True)
        ino_path = os.path.join(self.wiring_folder, "WIRING.ino")
        
        try:
            with open(ino_path, "w", encoding="utf-8") as f:
                f.write(codigo_cpp)
            self.log(f"Arquivo gerado: {ino_path}")
        except Exception as e:
            self.log(f"Erro ao salvar: {e}", "red")
            return

        # EXECUÇÃO DO ARDUINO-CLI (THREAD SEPARADA)
        threading.Thread(target=self._run_arduino_cli, args=(self.wiring_folder,), daemon=True).start()

    def _run_arduino_cli(self, path):
        """Chama o binário do arduino-cli localizado na pasta Engine"""
        if not os.path.exists(self.arduino_cli):
            self.log(f"Erro Crítico: arduino-cli não encontrado em {self.arduino_cli}", "red")
            return

        self.log("Compilador: Chamando arduino-cli...")
        
        try:
            # Comando padrão para Arduino Uno (Exemplo)
            comando = [self.arduino_cli, "compile", "--fqbn", "arduino:avr:uno", path]
            resultado = subprocess.run(comando, capture_output=True, text=True)

            if resultado.returncode == 0:
                self.log("SUCESSO: Código pronto para envio.", "#00ff00")
                self.log(resultado.stdout)
            else:
                self.log("ERRO NA COMPILAÇÃO ARDUINO:", "red")
                self.log(resultado.stderr, "#ffaaaa")

        except Exception as e:
            self.log(f"Falha na execução do motor: {e}", "red")

# Execução independente para testes do editor
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = WandiEditor()
    win.show()
    sys.exit(app.exec())