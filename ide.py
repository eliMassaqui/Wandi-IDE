import sys
import os
import threading
from PyQt6.QtWidgets import (
    QApplication, QMainWindow,
    QMenu, QToolBar, QComboBox, QPushButton,
    QTabWidget, QPlainTextEdit, QTextEdit,
    QDockWidget, QListWidget, QStackedWidget
)
from PyQt6.QtGui import QAction, QIcon, QFont
from PyQt6.QtCore import Qt, QUrl, QSize, pyqtSignal, QObject
from PyQt6.QtWebEngineWidgets import QWebEngineView

         # CORES #
# Gerenciador de biblioteca.
from CORE.BIBLIOTECA.wandilib import WandiLibManager
# MENU de ediçao do editor.
from CORE.MENU.wandimenu import WandiMenu
# Setup de init do arduino-cli.
from CORE.MOTOR.engine import initialize_wandi_engine 

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

    def _create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(35, 35)) 
        self.addToolBar(toolbar)
        icons_path = os.path.join(os.path.dirname(__file__), "icons")
        self.action_compilar = QAction(QIcon(os.path.join(icons_path, "compilar.png")), "Compilar", self)
        toolbar.addAction(self.action_compilar)
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
        board = QComboBox(); board.addItems(["Arduino Uno", "Arduino Mega"]); toolbar.addWidget(board)

    def _create_central(self):
        self.editor_tabs = QTabWidget()
        editor = QPlainTextEdit()
        editor.setPlainText("def setup():\n    pass\n\ndef loop():\n    pass")
        self.editor_tabs.addTab(editor, "wandicode.py")
        self.setCentralWidget(self.editor_tabs)

    def _create_console_dock(self):
        self.console_dock = QDockWidget("Mensageiro", self)
        tabs = QTabWidget()
        # Referenciando o output_widget para podermos escrever nele
        self.output_widget = QTextEdit()
        self.output_widget.setReadOnly(True)
        serial = QTextEdit(); serial.setReadOnly(True)
        tabs.addTab(self.output_widget, "Output")
        tabs.addTab(serial, "Serial")
        self.console_dock.setWidget(tabs)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.console_dock)

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

    def _adjust_initial_layout(self):
        largura_projeto = int(self.width() * 0.6)
        self.resizeDocks([self.project_dock], [largura_projeto], Qt.Orientation.Horizontal)

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
    app.setFont(QFont("Consolas", 13))
    load_style(app)
    window.showMaximized()
    sys.exit(app.exec())