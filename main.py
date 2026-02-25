import sys
import os
import threading
import subprocess

from PyQt6.QtWidgets import (
    QApplication, QMainWindow,
    QMenu, QToolBar, QComboBox, QPushButton,
    QTabWidget, QPlainTextEdit, QTextEdit,
    QDockWidget, QListWidget, QStackedWidget,
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QFrame, QLabel # <-- Adicionados
)

from PyQt6.QtGui import QAction, QIcon, QFont
from PyQt6.QtCore import Qt, QUrl, QSize, pyqtSignal, QObject, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView

from EDITOR.compilador import compiladorWandi

         # CORE #
from CORE.BIBLIOTECA.wandilib import WandiLibManager
from CORE.MENU.wandimenu import WandiMenu
from CORE.MOTOR.engine import initialize_wandi_engine
from CORE.LINHAS.linhas import WandiCodeLinhas
from CORE.SINTAXE.highlighter import WandiHighlighter
from CORE.NOTES.notificacoes import WandiNotificacao, WandiToast
from CORE.HARDWARE.hardware import obter_portas_disponiveis, ArduinoCLI, MonitorSerial

# Classe para desviar o print para o seu Output
# Print do Compilar e Upload também.
class ConsoleStream(QObject):
    text_written = pyqtSignal(str)
    def write(self, text):
        if text and text.strip():
            # Às vezes o stdout recebe objetos, forçamos string
            self.text_written.emit(str(text)) 
    def flush(self):
        pass

class WandiIDE(QMainWindow):
    def __init__(self):
        super().__init__()

        # 1. Definir caminhos (Realista)
        self.base_path = os.path.join(os.path.expanduser("~"), "Documents", "Wandi Studio", "Engine")
        self.cli_exe = os.path.join(self.base_path, "arduino", "arduino-cli.exe")
        self.wiring_folder = os.path.join(self.base_path, "WIRING")
        
        # --- NOVAS INTEGRAÇÕES ---
        self.arduino_cli = ArduinoCLI(self.cli_exe)
        self.thread_serial = None

        caminho_icone = os.path.join(os.path.dirname(__file__), "icons")
        self.setWindowIcon(QIcon(os.path.join(caminho_icone, "wandi.png")))

        self.setWindowTitle("Wandi IDE")
        self.resize(1200, 800)
        self.setCorner(Qt.Corner.BottomRightCorner, Qt.DockWidgetArea.RightDockWidgetArea)

        self._create_menu()
        self._create_toolbar()
        self._create_central()
        self._create_console_dock()
        self._create_project_dock()
        
        self._create_statusbar()
        self._adjust_initial_layout()
        self._apply_custom_styles()

        # 1. Definir caminhos (Realista)
        self.base_path = os.path.join(os.path.expanduser("~"), "Documents", "Wandi Studio", "Engine")
        self.cli_exe = os.path.join(self.base_path, "arduino", "arduino-cli.exe")
        self.wiring_folder = os.path.join(self.base_path, "WIRING")
        
        # 2. Inicializar tradutor
        self.tradutor = compiladorWandi()

        # --- INICIALIZAÇÃO DO MOTOR WANDI ---
        QTimer.singleShot(100, self.start_engine_check)

        self.toasts = [] # Lista para rastrear os cards ativos

    def start_engine_check(self):
        self.stream = ConsoleStream()
        
        # Conectamos o Toast primeiro
        self.stream.text_written.connect(self.gerenciar_notificacao) 
        # Depois o Output
        self.stream.text_written.connect(self.log_to_output)
        
        sys.stdout = self.stream 
        threading.Thread(target=initialize_wandi_engine, daemon=True).start()

    def gerenciar_notificacao(self, text):
        termos_toast = ["Sincronizando", "Instalando", "Provisionando", "Verificando", "✅"]
        
        # Verifica se a mensagem contém os termos, mesmo com HTML no meio
        if any(termo in text for termo in termos_toast):
            # NÃO limpamos o HTML aqui, apenas removemos espaços extras
            texto_formatado = text.strip() 
            
            # Criamos o Toast - o QLabel vai renderizar as cores do <font color="..."> automaticamente
            novo_toast = WandiToast(self, texto_formatado)
            self.toasts.append(novo_toast)
            self.reposicionar_toasts()

            if "✅" in text:
                QTimer.singleShot(30000, self.limpar_todos_toasts)
            else:
                QTimer.singleShot(10000, lambda: self.remover_toast(novo_toast))


    def reposicionar_toasts(self):
        # Lógica de empilhamento: o mais novo fica embaixo, empurrando os velhos para cima
        margem_direita = 20
        margem_inferior = 40
        espacamento = 10
        
        # Invertemos a lista para que o último criado fique na base
        for i, toast in enumerate(reversed(self.toasts)):
            x = self.width() - toast.width() - margem_direita
            # Calcula a altura acumulada
            y = self.height() - ( (toast.height() + espacamento) * (i + 1) ) - margem_inferior
            toast.move(x, y)

    def remover_toast(self, toast):
        if toast in self.toasts:
            self.toasts.remove(toast)
            toast.close()
            self.reposicionar_toasts()

    def limpar_todos_toasts(self):
        for toast in self.toasts[:]:
            self.remover_toast(toast)

    # Atualize também o resizeEvent para as notificações acompanharem a janela
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reposicionar_toasts()

    def log_to_output(self, text):
        # Termos que queremos que fiquem APENAS no Toast
        termos_motor = ["Sincronizando", "Instalando", "Provisionando", "Verificando", "✅", "Downloading"]
        
        # Se algum termo do motor estiver no texto, ignoramos para o Output
        if any(termo in text for termo in termos_motor):
            return

        # Se passou pelo filtro, escreve no console (Mensagens de compilação, etc)
        # Usamos insertHtml ou append para manter as cores caso a compilação também as tenha
        self.output_widget.setFont(QFont("Consolas", 10))
        self.output_widget.append(text) 
        self.output_widget.ensureCursorVisible()

    # --- SEUS MÉTODOS ORIGINAIS (SEM ALTERAÇÃO) ---

    def _apply_custom_styles(self):
        self.project_dock.setStyleSheet("""
            QDockWidget > QWidget { border-left: 1px solid #0078d4; background-color: #1e1e1e; }
            QDockWidget::title { background-color: #1e1e1e; border-left: 1px solid #0078d4; border-bottom: 1px solid #333; padding-left: 10px; color: #888; }
        """)
        self.console_dock.setStyleSheet("""
            QDockWidget > QWidget { border-top: 1px solid #555555; background-color: #1e1e1e; }
            QDockWidget::title { background-color: #1e1e1e; border-top: 1px solid #555555; border-bottom: 1px solid #333; padding-left: 10px; color: #888; }
        """)
        toolbar_style = """
            QToolBar { background: #252526; border-bottom: 2px solid #333; spacing: 10px; padding: 8px; }
            QToolButton, QPushButton { background-color: transparent; border: 2px solid #333; border-radius: 6px; padding: 3px; }
            QToolButton:hover, QPushButton:hover { background-color: #3e3e3e; border: 2px solid #0078d4; }
        """
        self.setStyleSheet(self.styleSheet() + toolbar_style)

    def _create_menu(self):
        self.menu_manager = WandiMenu(self)

    def disparar_compilacao(self):
        # (Seu código de tradução continua igual...)
        # ...
        # Em vez de chamar o seu antigo _run_cli_process, use:
        self.arduino_cli.compilar(self.wiring_folder, self.log_to_output)

    # ==========================================
    # LÓGICA DE INTEGRAÇÃO COM HARDWARE
    # ==========================================

    def atualizar_lista_portas(self):
        """Atualiza o dropdown com as portas conectadas fisicamente."""
        porta_atual = self.port.currentText()
        self.port.clear()
        
        portas = obter_portas_disponiveis()
        if portas:
            self.port.addItems(portas)
            # Tenta manter a porta que estava selecionada antes do refresh
            if porta_atual in portas:
                self.port.setCurrentText(porta_atual)
        else:
            self.port.addItem("Nenhuma porta")

    def disparar_upload(self):
        """Prepara os arquivos e aciona o upload via CLI."""
        porta = self.port.currentText()
        if porta == "Nenhuma porta" or not porta:
            self.log_to_output("❌ ERRO: Nenhuma placa Arduino detectada/selecionada.")
            return

        codigo_python = self.editor_tabs.currentWidget().toPlainText()
        codigo_cpp = self.tradutor.translate(codigo_python)
        
        if "ERRO" in codigo_cpp:
            self.log_to_output(f"Erro de Tradução: {codigo_cpp}")
            return

        os.makedirs(self.wiring_folder, exist_ok=True)
        ino_path = os.path.join(self.wiring_folder, "WIRING.ino")
        with open(ino_path, "w", encoding="utf-8") as f:
            f.write(codigo_cpp)

        # Chama a função de upload do nosso novo arquivo
        self.arduino_cli.upload(self.wiring_folder, porta, self.log_to_output)

    def alternar_conexao_serial(self):
        """Inicia ou encerra a leitura da porta serial."""
        if self.thread_serial and self.thread_serial.isRunning():
            # Se está rodando, vamos parar
            self.thread_serial.parar()
            self.thread_serial = None
            self.btn_conectar_serial.setText("Conectar")
            self.btn_conectar_serial.setStyleSheet("background-color: #0078d4; border: none; padding: 4px 10px; color: white;")
        else:
            # Se está parado, vamos tentar conectar
            porta = self.port.currentText()
            if porta == "Nenhuma porta":
                self.serial_widget.append("❌ Selecione uma porta primeiro.")
                return
                
            self.thread_serial = MonitorSerial(porta)
            
            # Conecta os sinais da Thread para a interface
            self.thread_serial.dados_recebidos.connect(lambda txt: self.serial_widget.append(txt))
            self.thread_serial.erro_serial.connect(lambda txt: self.serial_widget.append(txt))
            
            self.thread_serial.start()
            
            self.btn_conectar_serial.setText("Desconectar")
            self.btn_conectar_serial.setStyleSheet("background-color: #d40000; border: none; padding: 4px 10px; color: white;")
            
            # Garante que a aba Serial está visível para o usuário
            self.console_tabs.setCurrentIndex(1) 

    def enviar_comando_serial(self):
        """Pega o texto do input e manda para a placa via serial."""
        texto = self.serial_input.text()
        if self.thread_serial and self.thread_serial.isRunning() and texto.strip():
            self.thread_serial.enviar(texto)
            self.serial_input.clear()
        else:
            self.serial_widget.append("❌ Serial desconectada. Conecte antes de enviar comandos.")





    def _create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(35, 35)) 
        self.addToolBar(toolbar)
        icons_path = os.path.join(os.path.dirname(__file__), "icons")
        # ... código existente ...
        self.action_compilar = QAction(QIcon(os.path.join(icons_path, "compilar.png")), "Compilar", self)
        # CONEXÃO AQUI:
        self.action_compilar.triggered.connect(self.disparar_compilacao)
        toolbar.addAction(self.action_compilar)
        # ... restante da toolbar ...
        # Conectar o botão Enviar (Upload)
        self.action_enviar = QAction(QIcon(os.path.join(icons_path, "enviar.png")), "Enviar", self)
        self.action_enviar.triggered.connect(self.disparar_upload)
        toolbar.addAction(self.action_enviar)
        toolbar.addSeparator()
        self.btn_3d = QPushButton()
        self.btn_3d.setIcon(QIcon(os.path.join(icons_path, "3d.png")))
        self.btn_3d.setIconSize(QSize(39, 39)); self.btn_3d.setFixedSize(43, 43)
        self.btn_3d.clicked.connect(lambda: self._switch_view(0, "Simulação 3D"))
        toolbar.addWidget(self.btn_3d)
        self.btn_lib = QPushButton()
        self.btn_lib.setIcon(QIcon(os.path.join(icons_path, "biblioteca.png")))
        self.btn_lib.setIconSize(QSize(39, 39)); self.btn_lib.setFixedSize(43, 43)
        self.btn_lib.clicked.connect(lambda: self._switch_view(1, "Biblioteca"))
        toolbar.addWidget(self.btn_lib)
        toolbar.addSeparator()
        # Configuração Dinâmica das Portas
        self.port = QComboBox() 
        self.atualizar_lista_portas() # Preenche as portas na inicialização
        toolbar.addWidget(self.port)

        # Botão para atualizar a lista de portas manualmente
        self.btn_refresh_ports = QPushButton("↻") # Use texto ou um ícone de refresh se tiver
        self.btn_refresh_ports.setFixedSize(30, 30)
        self.btn_refresh_ports.setToolTip("Atualizar Portas")
        self.btn_refresh_ports.clicked.connect(self.atualizar_lista_portas)
        toolbar.addWidget(self.btn_refresh_ports)

    def _create_central(self):
            self.editor_tabs = QTabWidget()

             # Instancia a classe que está no widgets.py
            editor = WandiCodeLinhas() 
            editor.setFont(QFont("Consolas", 12))
            
            # Permite que as abas tenham o "X" para fechar
            self.editor_tabs.setTabsClosable(True)
            # Conecta o clique no "X" à função de remover
            self.editor_tabs.tabCloseRequested.connect(self._fechar_aba)

            # ... resto do seu código (instanciar editor, highlighter, etc) ...
            editor = WandiCodeLinhas() 
            self.editor_tabs.addTab(editor, "Código Wandi")
            self.setCentralWidget(self.editor_tabs)
            self.highlighter = WandiHighlighter(editor.document())
            editor.setPlainText("def setup():\n   pass\n\ndef loop():\n   pass")

    def _fechar_aba(self, index):
        # Impede fechar se for a última aba (opcional, mantém a IDE funcional)
        if self.editor_tabs.count() <= 1:
            self.statusBar().showMessage("Não é possível fechar a última aba de código.")
            return

        # Remove a aba pelo índice recebido
        self.editor_tabs.removeTab(index)
        self.statusBar().showMessage("Aba removida.")

    def _create_console_dock(self):
        self.console_dock = QDockWidget("Mensageiro", self)
        # Criamos o TabWidget
        self.console_tabs = QTabWidget() 
        
        # --- ESTILO FLAT (SEM LINHAS) ---
        style_flat = """
            QTabWidget::pane { border: none; }
            QPushButton#btnLimpar {
                background-color: transparent;
                color: #888888;
                border: none;
                padding: 0px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton#btnLimpar:hover { color: #ffffff; }
            QLineEdit { background-color: #2d2d2d; color: #ffffff; border: none; padding: 4px; }
            QTextEdit { background-color: #1e1e1e; border: none; color: #d4d4d4; }
        """
        self.console_tabs.setStyleSheet(style_flat)

        # --- ABA OUTPUT ---
        self.output_widget = QTextEdit()
        self.output_widget.setReadOnly(True)
        self.console_tabs.addTab(self.output_widget, "Output")

        # --- ABA SERIAL ---
        serial_tab = QWidget()
        ser_layout = QVBoxLayout(serial_tab)
        ser_layout.setContentsMargins(0, 5, 0, 0)
        
        input_container = QHBoxLayout()
        
        # Novo Botão Conectar/Desconectar
        self.btn_conectar_serial = QPushButton("Conectar")
        self.btn_conectar_serial.setStyleSheet("background-color: #0078d4; border: none; padding: 4px 10px; color: white;")
        self.btn_conectar_serial.clicked.connect(self.alternar_conexao_serial)
        
        self.serial_input = QLineEdit()
        self.serial_input.setPlaceholderText("Enviar comando...")
        # Permite enviar apertando "Enter"
        self.serial_input.returnPressed.connect(self.enviar_comando_serial) 
        
        btn_enviar = QPushButton("Enviar")
        btn_enviar.setStyleSheet("background-color: #333; border: none; padding: 4px 10px;")
        btn_enviar.clicked.connect(self.enviar_comando_serial)
        
        input_container.addWidget(self.btn_conectar_serial)
        input_container.addWidget(self.serial_input)
        input_container.addWidget(btn_enviar)
        
        self.serial_widget = QTextEdit()
        self.serial_widget.setReadOnly(True)
        
        ser_layout.addLayout(input_container)
        ser_layout.addWidget(self.serial_widget)
        self.console_tabs.addTab(serial_tab, "Serial")

        # --- O PULO DO GATO: BOTÃO NO CANTO DA BARRA ---
        btn_limpar_geral = QPushButton("LIMPAR")
        btn_limpar_geral.setObjectName("btnLimpar")
        btn_limpar_geral.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Função para limpar a aba que estiver aberta no momento
        btn_limpar_geral.clicked.connect(self._limpar_aba_atual)
        
        # Coloca o botão no canto superior direito da barra de abas
        self.console_tabs.setCornerWidget(btn_limpar_geral, Qt.Corner.TopRightCorner)

        self.console_dock.setWidget(self.console_tabs)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.console_dock)

    def _limpar_aba_atual(self):
        # Verifica qual aba está selecionada e limpa o widget correspondente
        index = self.console_tabs.currentIndex()
        if index == 0: # Aba Output
            self.output_widget.clear()
        elif index == 1: # Aba Serial
            self.serial_widget.clear()

    def _create_project_dock(self):
        self.project_dock = QDockWidget("Simulação 3D", self)
        self.project_stack = QStackedWidget()
        self.simulation_view = QWebEngineView()
        self.simulation_view.load(QUrl("https://simulation-one.vercel.app/"))
        self.library_manager = WandiLibManager()
        self.project_stack.addWidget(self.simulation_view)
        self.project_stack.addWidget(self.library_manager)
        self.project_dock.setWidget(self.project_stack)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.project_dock)
        self.project_dock.hide()

    def _switch_view(self, index, title):
        self.project_stack.setCurrentIndex(index)
        self.project_dock.setWindowTitle(title)
        self.project_dock.show()

        # Personalização dinâmica de largura:
        if index == 0:  # Simulação 3D
            largura = 800  # Simulação costuma ser maior
        else:           # Biblioteca
            largura = 350  # Biblioteca pode ser mais estreita

        # Aplica o redimensionamento
        self.resizeDocks([self.project_dock], [largura], Qt.Orientation.Horizontal)

    def _adjust_initial_layout(self):
        # 1. Define a altura do Mensageiro (Vertical)
        self.resizeDocks([self.console_dock], [220], Qt.Orientation.Vertical)

        # 2. Define a largura inicial do Dock da direita (Horizontal)
        # Como ele começa oculto ou na simulação, definimos um padrão
        self.resizeDocks([self.project_dock], [500], Qt.Orientation.Horizontal)

        # --- PERSONALIZAÇÃO DA ALTURA DO MENSAGEIRO ---
        # Define a altura desejada (ex: 200 pixels)
        altura_mensageiro = 220
        self.resizeDocks([self.console_dock], [altura_mensageiro], Qt.Orientation.Vertical)

    def _create_statusbar(self):
        self.statusBar().showMessage("Pronto")

def load_style(app):
    try:
        if os.path.exists("style/dark.qss"):
            with open("style/dark.qss", "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
    except Exception as e: print(f"Erro ao carregar estilo: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WandiIDE()
    app.setFont(QFont("Consolas", 14))
    load_style(app)
    window.showMaximized()
    sys.exit(app.exec())