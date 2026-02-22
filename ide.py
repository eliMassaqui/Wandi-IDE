import sys
import os
import threading
import subprocess

from PyQt6.QtWidgets import (
    QApplication, QMainWindow,
    QMenu, QToolBar, QComboBox, QPushButton,
    QTabWidget, QPlainTextEdit, QTextEdit,
    QDockWidget, QListWidget, QStackedWidget,
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit # <-- Adicionados
)

from PyQt6.QtGui import QAction, QIcon, QFont
from PyQt6.QtCore import Qt, QUrl, QSize, pyqtSignal, QObject
from PyQt6.QtWebEngineWidgets import QWebEngineView

from EDITOR.compilador import compiladorWandi

         # CORE #
from CORE.BIBLIOTECA.wandilib import WandiLibManager
from CORE.MENU.wandimenu import WandiMenu
from CORE.MOTOR.engine import initialize_wandi_engine
from CORE.LINHAS.linhas import WandiCodeLinhas
from CORE.SINTAXE.highlighter import WandiHighlighter


# Classe para desviar o print para o seu Output
# Print do Compilar e Upload também.
class ConsoleStream(QObject):
    text_written = pyqtSignal(str)
    def write(self, text):
        if text.strip():
            self.text_written.emit(text)
    def flush(self):
        pass

class WandiIDE(QMainWindow):
    def __init__(self):
        super().__init__()

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
        self.start_engine_check()

    def start_engine_check(self):
        # Redireciona o print para a aba Output
        self.stream = ConsoleStream()
        self.stream.text_written.connect(self.log_to_output)
        sys.stdout = self.stream 

        # Roda em thread para não travar a UI original
        threading.Thread(target=initialize_wandi_engine, daemon=True).start()

    def log_to_output(self, text):
            # Garante fonte de console para os logs técnicos
            self.output_widget.setFont(QFont("Consolas", 10))
            self.output_widget.append(text)
            
            # Scroll automático
            self.output_widget.ensureCursorVisible()

            # Se houver atividade técnica pesada, abre o dock "Mensageiro"
            termos_tecnicos = ["Updating", "Downloading", "Installing", "Configuring", "Extracting"]
            if any(termo in text for termo in termos_tecnicos):
                if self.console_dock.isHidden():
                    self.console_dock.show()

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
        # Pega o código Python que está escrito no editor de texto
        codigo_python = self.editor_tabs.currentWidget().toPlainText()
        
        self.log_to_output("--- [Wandi Engine] Iniciando Compilação ---")
        
        # PASSO 1: TRADUÇÃO
        codigo_cpp = self.tradutor.translate(codigo_python)
        if "ERRO" in codigo_cpp:
            self.log_to_output(f"Erro de Tradução: {codigo_cpp}")
            return

        # PASSO 2: SALVAR O .INO
        os.makedirs(self.wiring_folder, exist_ok=True)
        ino_path = os.path.join(self.wiring_folder, "WIRING.ino")
        with open(ino_path, "w", encoding="utf-8") as f:
            f.write(codigo_cpp)

        # PASSO 3: RODAR ARDUINO-CLI (Em thread para não travar a tela)
        threading.Thread(target=self._run_cli_process, args=(self.wiring_folder,), daemon=True).start()

    def _run_cli_process(self, path):
        try:
            # Comando para compilar para Arduino Uno
            cmd = [self.cli_exe, "compile", "--fqbn", "arduino:avr:uno", path]
            processo = subprocess.run(cmd, capture_output=True, text=True)

            if processo.returncode == 0:
                self.log_to_output("✔ SUCESSO: Código compilado e pronto!")
                self.log_to_output(processo.stdout)
            else:
                self.log_to_output("❌ ERRO NA COMPILAÇÃO:")
                self.log_to_output(processo.stderr)
        except Exception as e:
            self.log_to_output(f"Erro ao chamar compilador: {e}")

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
        self.action_enviar = QAction(QIcon(os.path.join(icons_path, "enviar.png")), "Enviar", self)
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
        port = QComboBox(); port.addItems(["COM5", "COM6"]); toolbar.addWidget(port)

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
        ser_layout.setContentsMargins(0, 5, 0, 0) # Ajuste para o input colado no topo
        
        input_container = QHBoxLayout()
        self.serial_input = QLineEdit()
        self.serial_input.setPlaceholderText("Enviar comando...")
        btn_enviar = QPushButton("Enviar")
        btn_enviar.setStyleSheet("background-color: #333; border: none; padding: 4px 10px;")
        
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