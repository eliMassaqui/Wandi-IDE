import os
import sys
import subprocess
import platform
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QLabel, QFrame, QScrollArea,
    QComboBox, QDialog, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve

# --- MANTENDO SUA LÓGICA DE CAMINHOS ORIGINAL ---
user_docs = os.path.join(os.path.expanduser('~'), "Documents")
work_dir = os.path.join(user_docs, "Wandi Studio", "Engine", "arduino")
config_file = os.path.join(work_dir, "arduino-cli.yaml")
exe_name = "arduino-cli.exe" if platform.system().lower() == "windows" else "arduino-cli"
exe_path = os.path.join(work_dir, exe_name)

# --- COMPONENTE DE CHIP COM LÓGICA DE SELEÇÃO ---
class FilterChip(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(30)
        self.set_active(False)

    def set_active(self, active=False):
        if active:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border: 1px solid #005a9e;
                    border-radius: 15px;
                    padding: 0px 15px;
                    font-size: 12px;
                    font-weight: bold;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #333;
                    color: #bbb;
                    border: 1px solid #444;
                    border-radius: 15px;
                    padding: 0px 15px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #444;
                    border: 1px solid #0078d4;
                    color: white;
                }
            """)

# --- CARD SUSPENSO MODERNO ---
class InstallDialog(QDialog):
    def __init__(self, lib_data, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.lib_name = lib_data.get("name", "Biblioteca")
        self.lib_author = lib_data.get("author") or lib_data.get("latest", {}).get("author", "Comunidade")
        self.lib_desc = lib_data.get("sentence") or lib_data.get("latest", {}).get("sentence", "Esta biblioteca está pronta para ser integrada.")
        
        self.selected_version = None
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(500)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.init_ui(lib_data)
        self.anim.start()

    def init_ui(self, data):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        self.container = QFrame()
        self.container.setObjectName("ModernCard")
        self.container.setFixedWidth(450)
        self.container.setStyleSheet("""
            QFrame#ModernCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                            stop:0 rgba(0, 120, 212, 255), 
                            stop:0.7 rgba(20, 20, 25, 250),
                            stop:1 rgba(255, 255, 255, 50));
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 25px;
            }
            QLabel { color: #ffffff; background: transparent; }
            #LibTitle { font-size: 24px; font-weight: bold; color: #ffffff; }
            #LibAuthor { color: rgba(255, 255, 255, 0.6); font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }
            #LibDesc { color: #e0e0e0; font-size: 13px; line-height: 18px; margin: 5px 0px; }
            QComboBox { background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 10px; padding: 10px; color: white; font-size: 14px; min-height: 25px; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background-color: #1e1e1e; color: white; selection-background-color: #0078d4; }
            QPushButton#BtnInstall { background: #ffffff; color: #0078d4; border-radius: 12px; padding: 12px; font-weight: bold; font-size: 14px; border: none; }
            QPushButton#BtnInstall:hover { background: #0078d4; color: #ffffff; border: 1px solid white; }
            QPushButton#BtnClose { background: transparent; color: rgba(255,255,255,0.5); font-size: 12px; border: none; }
            QPushButton#BtnClose:hover { color: white; }
        """)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(35, 35, 35, 35)
        layout.setSpacing(18)

        title = QLabel(self.lib_name)
        title.setObjectName("LibTitle")
        title.setWordWrap(True)
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        author = QLabel(f"Por: {self.lib_author}")
        author.setObjectName("LibAuthor")
        layout.addWidget(author, alignment=Qt.AlignmentFlag.AlignCenter)

        desc = QLabel(self.lib_desc)
        desc.setObjectName("LibDesc")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        layout.addWidget(QLabel("Selecione a versão:"), alignment=Qt.AlignmentFlag.AlignLeft)
        self.combo = QComboBox()
        releases = data.get("releases", {})
        versoes = sorted(list(releases.keys()), reverse=True)
        self.combo.addItems(versoes)
        layout.addWidget(self.combo)

        layout.addSpacing(10)
        btn_install = QPushButton("INSTALAR AGORA")
        btn_install.setObjectName("BtnInstall")
        btn_install.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_install.clicked.connect(self.accept_install)
        layout.addWidget(btn_install)

        btn_close = QPushButton("Cancelar e voltar")
        btn_close.setObjectName("BtnClose")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.reject)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(self.container, alignment=Qt.AlignmentFlag.AlignCenter)

    def accept_install(self):
        self.selected_version = self.combo.currentText()
        self.accept()

# --- WORKER ORIGINAL ---
class ArduinoWorker(QThread):
    finished = pyqtSignal(dict)

    def __init__(self, args):
        super().__init__()
        self.args = args

    def run(self):
        try:
            cmd = [exe_path] + self.args + ["--config-file", config_file, "--format", "json"]
            result = subprocess.run(cmd, cwd=work_dir, capture_output=True, text=True, encoding="utf-8", errors="replace")
            
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    self.finished.emit(data)
                except json.JSONDecodeError:
                    self.finished.emit({"success": True, "log": result.stdout})
            else:
                self.finished.emit({"error": result.stderr or "Sem resposta do CLI."})
        except Exception as e:
            self.finished.emit({"error": str(e)})

# --- CARD DA LISTA ---
class LibCard(QFrame):
    def __init__(self, data, is_installed, is_search_mode, parent_manager):
        super().__init__()
        self.manager = parent_manager
        self.raw_data = data 
        
        latest = data.get("latest", {})
        self.lib_name = data.get("name") or latest.get("name", "Desconhecido")
        author = data.get("author") or latest.get("author", "Autor desconhecido")
        desc_text = data.get("sentence") or latest.get("sentence", "Sem descrição.")
        version = data.get("version") or latest.get("version", "N/A")

        self.setObjectName("LibCard")
        self.setStyleSheet("""
            QFrame#LibCard { 
                background-color: #252525; border-radius: 8px; 
                border: 1px solid #333; margin-bottom: 2px;
            }
            QFrame#LibCard:hover {
                background-color: #2b2b2b; border: 1px solid #0078d4;
            }
        """)
        
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        name_label = QLabel(self.lib_name)
        name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #0078d4; background: transparent; border: none;")
        
        ver_label = QLabel(f"v{version}")
        ver_label.setStyleSheet("color: #777; font-size: 10px; background: transparent; border: none;")
        
        header.addWidget(name_label)
        header.addStretch()
        header.addWidget(ver_label)
        layout.addLayout(header)
        
        auth_label = QLabel(f"Por: {author}")
        auth_label.setStyleSheet("color: #888; font-style: italic; font-size: 10px; background: transparent; border: none;")
        layout.addWidget(auth_label)
        
        desc_label = QLabel(desc_text)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #bbb; font-size: 11px; margin-top: 5px; background: transparent; border: none;")
        layout.addWidget(desc_label)
        
        self.btn_action = QPushButton("Remover" if is_installed else "Instalar")
        btn_base_color = "#d83b01" if is_installed else "#0078d4"
        self.btn_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_action.setStyleSheet(f"QPushButton {{ background-color: {btn_base_color}; color: white; font-weight: bold; border-radius: 4px; padding: 4px 12px; border: none; }}")
        
        self.btn_action.clicked.connect(self.on_click)
        layout.addWidget(self.btn_action, alignment=Qt.AlignmentFlag.AlignRight)

    def on_click(self):
        if "Remover" in self.btn_action.text():
            action = ["lib", "uninstall", self.lib_name]
            self.manager.handle_action(action)
        else:
            dialog = InstallDialog(self.raw_data, self.manager)
            if dialog.exec():
                version = dialog.selected_version
                action = ["lib", "install", f"{self.lib_name}@{version}"]
                self.manager.handle_action(action)

# --- GERENCIADOR PRINCIPAL (WIDGET DE EXPORTAÇÃO) ---
class WandiLibManager(QWidget):
    def __init__(self):
        super().__init__()
        self.pending_libs = []
        self.all_chips = []
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #1e1e1e; color: #ffffff; font-family: 'Segoe UI', sans-serif; }
            QLineEdit { background-color: #2d2d2d; border: 1px solid #333; padding: 8px; border-radius: 4px; color: white; }
            QPushButton#MainBtn { background-color: #333; padding: 8px 15px; border-radius: 4px; font-weight: bold; color: white; border: none; }
            QPushButton#MainBtn:hover { background-color: #444; }
        """)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)

        search_area = QVBoxLayout()
        search_input_row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Pesquisar bibliotecas...")
        self.input.returnPressed.connect(self.do_search)
        self.btn_s = QPushButton("Buscar")
        self.btn_s.setObjectName("MainBtn")
        self.btn_s.clicked.connect(self.do_search)
        search_input_row.addWidget(self.input, stretch=1)
        search_input_row.addWidget(self.btn_s)
        search_area.addLayout(search_input_row)

        chips_layout = QHBoxLayout()
        chips_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        filtros = ["Stepper", "Liquid", "Servo", "Sensor", "Display"]
        for nome in filtros:
            chip = FilterChip(nome)
            chip.clicked.connect(lambda checked, n=nome: self.chip_search(n))
            chips_layout.addWidget(chip)
            self.all_chips.append(chip)
        search_area.addLayout(chips_layout)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #0078d4; font-size: 11px;")
        search_area.addWidget(self.status_label)
        self.main_layout.addLayout(search_area)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background: transparent;")
        self.container_widget = QWidget()
        self.card_layout = QVBoxLayout(self.container_widget)
        self.card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.container_widget)
        self.main_layout.addWidget(self.scroll)

        self.btn_more = QPushButton("Carregar mais resultados...")
        self.btn_more.hide()
        self.card_layout.addWidget(self.btn_more)

        self.btn_list = QPushButton("Ver Bibliotecas Instaladas")
        self.btn_list.setObjectName("MainBtn")
        self.btn_list.clicked.connect(self.load_installed)
        self.main_layout.addWidget(self.btn_list)

        self.load_installed()

    def update_chip_styles(self, current_term):
        for chip in self.all_chips:
            chip.set_active(chip.text().lower() == current_term.lower())

    def chip_search(self, term):
        self.input.setText(term)
        self.do_search()

    def do_search(self):
        txt = self.input.text().strip()
        if txt:
            self.update_chip_styles(txt)
            self.btn_more.hide()
            self.update_status(f"🔍 Pesquisando: {txt}...")
            self.worker = ArduinoWorker(["lib", "search", txt])
            self.worker.finished.connect(lambda d: self.prepare_render(d, False, True))
            self.worker.start()

    def load_installed(self):
        self.update_chip_styles("")
        self.btn_more.hide()
        self.update_status("📂 Carregando instaladas...")
        self.worker = ArduinoWorker(["lib", "list"])
        self.worker.finished.connect(lambda d: self.prepare_render(d, True, False))
        self.worker.start()

    def update_status(self, text):
        self.status_label.setText(text)

    def prepare_render(self, data, installed, is_search):
        for i in reversed(range(self.card_layout.count())):
            widget = self.card_layout.itemAt(i).widget()
            if widget and widget != self.btn_more:
                widget.deleteLater()

        libs = data.get("libraries", []) if not installed else data.get("installed_libraries", [])
        self.pending_libs = libs
        self.current_is_installed = installed
        self.current_is_search = is_search
        self.process_render_queue()

    def process_render_queue(self):
        lote_size = 20
        self.card_layout.removeWidget(self.btn_more)
        for _ in range(lote_size):
            if not self.pending_libs: break
            lib = self.pending_libs.pop(0)
            item_data = lib.get("library", lib)
            card = LibCard(item_data, self.current_is_installed, self.current_is_search, self)
            self.card_layout.addWidget(card)
        self.card_layout.addWidget(self.btn_more)
        self.update_status("✅ Pronto.")

    def handle_action(self, args):
        self.update_status("⚙️ Processando...")
        self.worker = ArduinoWorker(args)
        self.worker.finished.connect(lambda d: self.load_installed())
        self.worker.start()

# --- EXECUÇÃO SOLO APENAS PARA TESTES ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = WandiLibManager()
    win.show()
    sys.exit(app.exec())