import sys
import os
import threading

from PyQt6.QtWidgets import (
    QApplication, QMainWindow,
    QMenu, QToolBar, QComboBox, QPushButton,
    QTabWidget, QTextEdit,
    QDockWidget, QStackedWidget,
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit
)
from PyQt6.QtGui import QAction, QIcon, QFont
from PyQt6.QtCore import Qt, QUrl, QSize, pyqtSignal, QObject, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel

# Suas importações internas
from COMPILADOR.compilador import compiladorWandi
from CORE.BIBLIOTECA.wandilib import WandiLibManager
from CORE.MENU.wandimenu import WandiMenu
from CORE.MOTOR.engine import initialize_wandi_engine
from CORE.LINHAS.linhas import WandiCodeLinhas
from CORE.SINTAXE.highlighter import WandiHighlighter
from CORE.NOTES.notificacoes import WandiToast
from CORE.HARDWARE.hardware import obter_portas_disponiveis, ArduinoCLI, MonitorSerial
from CORE.BRIDGE.wandi_bridge import WandiBridge

class ConsoleStream(QObject):
    """Desvia o print (stdout) para emitir sinais capturáveis pela GUI."""
    text_written = pyqtSignal(str)
    
    def write(self, text):
        if text and text.strip():
            self.text_written.emit(str(text)) 
            
    def flush(self):
        pass


class WandiIDE(QMainWindow):
    # Sinal para atualizar o log com segurança entre threads
    signal_log = pyqtSignal(str)
    def __init__(self):
        super().__init__()

        self.web_bridge = WandiBridge(self) # Inicializa o servidor WebSocket

        # Conectar o sinal ao método real de escrita
        self.signal_log.connect(self._escrever_no_log)

        # --- CAMINHOS E FERRAMENTAS ---
        self.base_path = os.path.join(os.path.expanduser("~"), "Documents", "Wandi Studio", "Engine")
        self.cli_exe = os.path.join(self.base_path, "arduino", "arduino-cli.exe")
        self.wiring_folder = os.path.join(self.base_path, "WIRING")

        # Carregar última sessão
        self.current_file_path = None 
        self.session_file = os.path.join(self.base_path, "last_session.txt") # Guarda o caminho do último arquivo aberto

        # --- CONFIGURAÇÃO DO AUTO-SAVE (30 SEGUNDOS) ---
        self.timer_autosave = QTimer(self)
        self.timer_autosave.timeout.connect(self._executar_autosave)
        self.timer_autosave.start(30000) # 30000 ms = 30 segundos

        # Modifique o final do __init__ ou o singleShot:
        QTimer.singleShot(100, self._carregar_ultima_sessao)
        
        self.arduino_cli = ArduinoCLI(self.cli_exe)
        self.thread_serial = None
        self.tradutor = compiladorWandi()
        self.toasts = []

        # --- CONFIGURAÇÃO DA JANELA ---
        caminho_icone = os.path.join(os.path.dirname(__file__), "icons")
        self.setWindowIcon(QIcon(os.path.join(caminho_icone, "wandi.png")))
        self.setWindowTitle("Wandi IDE")
        self.resize(1200, 800)
        self.setCorner(Qt.Corner.BottomRightCorner, Qt.DockWidgetArea.RightDockWidgetArea)

        # --- CONSTRUÇÃO DA UI ---
        self._create_menu()
        self._create_toolbar(caminho_icone)
        self._create_central()
        self._create_console_dock()
        self._create_project_dock()
        self._create_statusbar()
        self._adjust_initial_layout()
        self._apply_custom_styles()

        # --- INICIALIZAÇÃO DO MOTOR ---
        QTimer.singleShot(100, self.start_engine_check)

    # ==========================================
    # MOTOR E NOTIFICAÇÕES
    # ==========================================
    def start_engine_check(self):
        self.stream = ConsoleStream()
        self.stream.text_written.connect(self.gerenciar_notificacao) 
        self.stream.text_written.connect(self.log_to_output)
        
        sys.stdout = self.stream 
        threading.Thread(target=initialize_wandi_engine, daemon=True).start()

    def gerenciar_notificacao(self, text):
        termos_toast = ["Sincronizando", "Instalando", "Provisionando", "Verificando", "✅"]
        if any(termo in text for termo in termos_toast):
            texto_formatado = text.strip() 
            novo_toast = WandiToast(self, texto_formatado)
            self.toasts.append(novo_toast)
            self.reposicionar_toasts()

            if "✅" in text:
                QTimer.singleShot(20000, self.limpar_todos_toasts)
            else:
                QTimer.singleShot(3000, lambda: self.remover_toast(novo_toast))

    def reposicionar_toasts(self):
        margem_direita, margem_inferior, espacamento = 20, 40, 10
        for i, toast in enumerate(reversed(self.toasts)):
            x = self.width() - toast.width() - margem_direita
            y = self.height() - ((toast.height() + espacamento) * (i + 1)) - margem_inferior
            toast.move(x, y)

    def remover_toast(self, toast):
        if toast in self.toasts:
            self.toasts.remove(toast)
            toast.close()
            self.reposicionar_toasts()

    def limpar_todos_toasts(self):
        for toast in self.toasts[:]:
            self.remover_toast(toast)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reposicionar_toasts()

    def log_to_output(self, text):
        """Método chamado pelas threads (ArduinoCLI, etc)"""
        if not text: return
        
        # Sua lógica original de filtros
        termos_motor = ["Sincronizando", "Instalando", "Provisionando", "Verificando", "✅", "Downloading"]
        if any(termo in text for termo in termos_motor):
            return

        # Emite o sinal. O PyQt jogará isso para a thread principal automaticamente.
        self.signal_log.emit(text)

    def _escrever_no_log(self, text):
        """Método que roda apenas na Thread da UI (Seguro)"""
        self.output_widget.setFont(QFont("Consolas", 10))
        self.output_widget.append(text)
        
        # Agora o ensureCursorVisible funciona perfeitamente pois estamos na thread certa
        cursor = self.output_widget.textCursor()
        self.output_widget.moveCursor(cursor.MoveOperation.End)

    def _carregar_ultima_sessao(self):
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, "r", encoding="utf-8") as f:
                    path = f.read().strip()
                    if path and os.path.exists(path):
                        # Em vez de abrir uma nova aba, atualizamos a que já existe
                        with open(path, "r", encoding="utf-8") as file_content:
                            conteudo = file_content.read()
                            
                        editor = self.editor_tabs.currentWidget()
                        if editor:
                            editor.setPlainText(conteudo)
                            self.current_file_path = path
                            self.editor_tabs.setTabText(0, os.path.basename(path))
                        return
            except Exception as e:
                self.log_to_output(f"Erro ao restaurar sessão: {e}")

    def _executar_autosave(self):
            # Percorre todas as abas abertas no editor
            for i in range(self.editor_tabs.count()):
                titulo_aba = self.editor_tabs.tabText(i)
                
                # Se a aba tem o asterisco, ela precisa ser salva
                if "*" in titulo_aba:
                    editor = self.editor_tabs.widget(i)
                    
                    # Precisamos saber o caminho desse arquivo específico.
                    # Como você pode ter várias abas, o ideal é que cada editor guarde seu próprio caminho.
                    # Se ainda não implementou isso, usaremos uma verificação de segurança:
                    if hasattr(self, 'current_file_path') and self.current_file_path:
                        # Se for a aba principal/atual
                        if i == self.editor_tabs.currentIndex():
                            self.menu_manager._guardar_arquivo()
                        else:
                            # Para abas em segundo plano, salvamos silenciosamente
                            self._salvar_aba_especifica(i)


    def _salvar_aba_especifica(self, index):
        editor = self.editor_tabs.widget(index)
        nome_arquivo = self.editor_tabs.tabText(index).replace("*", "")
        
        # Tenta encontrar o caminho completo para esse arquivo na sua pasta padrão
        caminho = os.path.join(self.menu_manager.default_dir, nome_arquivo)
        
        if os.path.exists(caminho):
            try:
                with open(caminho, "w", encoding="utf-8") as f:
                    f.write(editor.toPlainText())
                self.editor_tabs.setTabText(index, nome_arquivo)
            except Exception as e:
                print(f"Erro no auto-save da aba {index}: {e}")

    def marcar_como_modificado(self):
        """Adiciona um asterisco ao título da aba se o conteúdo for alterado."""
        index = self.editor_tabs.currentIndex()
        if index == -1:
            return
            
        texto_atual = self.editor_tabs.tabText(index)
        
        # Só adiciona o asterisco se ele ainda não estiver lá
        if not texto_atual.endswith("*"):
            self.editor_tabs.setTabText(index, texto_atual + "*")

    # ==========================================
    # INTEGRAÇÃO COM HARDWARE
    # ==========================================
    def atualizar_lista_portas(self):
        porta_atual = self.port.currentText()
        self.port.clear()
        
        portas = obter_portas_disponiveis()
        if portas:
            self.port.addItems(portas)
            if porta_atual in portas:
                self.port.setCurrentText(porta_atual)
        else:
            self.port.addItem("Nenhuma porta")

    def preparar_pasta_wiring(self):
        """Método auxiliar para traduzir e salvar o arquivo .ino antes do hardware."""
        editor = self.editor_tabs.currentWidget()
        if not editor: return False
        
        codigo_python = editor.toPlainText()
        codigo_cpp = self.tradutor.translate(codigo_python)
        
        if "ERRO" in codigo_cpp:
            self.log_to_output(f"❌ Erro de Tradução: {codigo_cpp}")
            return False

        try:
            os.makedirs(self.wiring_folder, exist_ok=True)
            ino_path = os.path.join(self.wiring_folder, "WIRING.ino")
            with open(ino_path, "w", encoding="utf-8") as f:
                f.write(codigo_cpp)
            return True
        except Exception as e:
            self.log_to_output(f"❌ Erro ao gravar arquivo: {e}")
            return False

    def disparar_compilacao(self):
        # 1. Salva o .py original
        self.menu_manager._guardar_arquivo()
        
        # 2. Traduz para .ino (Essencial para o compilador ler o código novo)
        if self.preparar_pasta_wiring():
            self.statusBar().showMessage("Compilando código...")
            self.arduino_cli.compilar(self.wiring_folder, self.log_to_output)

    def disparar_upload(self):
        self.menu_manager._guardar_arquivo()
        porta = self.port.currentText()
        
        if porta == "Nenhuma porta" or not porta:
            self.log_to_output("❌ Erro: Selecione uma porta serial antes do Upload.")
            return

        # Traduz e prepara (conforme sua lógica)
        if not self.preparar_pasta_wiring():
            return

        self.log_to_output("--- Iniciando Ciclo: Compilação -> Upload ---")
        
        def callback_verificador(mensagem):
            # Este callback vem da thread do subprocesso, mas o sinal resolve o crash
            self.log_to_output(mensagem) 
            if "✔ SUCESSO: Código compilado!" in mensagem:
                self.arduino_cli.upload(self.wiring_folder, porta, self.log_to_output)

        self.arduino_cli.compilar(self.wiring_folder, callback_verificador)

    def alternar_conexao_serial(self):
            if self.thread_serial and self.thread_serial.isRunning():
                # 1. Desconecta os sinais para evitar que a thread fale com a UI enquanto morre
                try:
                    self.thread_serial.dados_recebidos.disconnect()
                except:
                    pass
                
                # 2. Para a thread e espera um pouco (evita o erro de wait on itself)
                self.thread_serial.parar()
                self.thread_serial.wait(300) # Dá 300ms para fechar a porta com calma
                self.thread_serial = None
                
                # 3. Notifica a Web
                self.web_bridge.send_to_web("STATUS:OFF")
                self._atualizar_ui_serial_desconectado()
                self.simulation_view.reload() 
                
            else:
                porta = self.port.currentText()
                if porta == "Nenhuma porta" or not porta: 
                    return
                    
                # Cria a nova thread
                self.thread_serial = MonitorSerial(porta)
                
                # Conecta o sinal ANTES de iniciar
                self.thread_serial.dados_recebidos.connect(self.web_bridge.send_to_web)
                self.thread_serial.start()
                
                # Sincroniza a Web
                self.simulation_view.reload() 
                
                # Pequeno delay para garantir que o servidor WebSocket está pronto para a nova conexão
                self.web_bridge.send_to_web("STATUS:ON")
                self._atualizar_ui_serial_conectado()

    def enviar_comando_serial(self):
        texto = self.serial_input.text().strip()
        if self.thread_serial and self.thread_serial.isRunning() and texto:
            self.thread_serial.enviar(texto)
            self.serial_input.clear()
        else:
            self.serial_widget.append("❌ Serial desconectada ou comando em branco.")

    def _atualizar_ui_serial_conectado(self):
        self.btn_conectar_serial.setText("Desconectar")
        self.btn_conectar_serial.setStyleSheet("background-color: #d40000; border: none; padding: 4px 10px; color: white;")

    def _atualizar_ui_serial_desconectado(self):
        self.btn_conectar_serial.setText("Conectar")
        self.btn_conectar_serial.setStyleSheet("background-color: #0078d4; border: none; padding: 4px 10px; color: white;")

    # ==========================================
    # CONSTRUÇÃO DA INTERFACE (UI)
    # ==========================================
    def _create_menu(self):
        self.menu_manager = WandiMenu(self)

    def _create_toolbar(self, icons_path):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(35, 35)) 
        self.addToolBar(toolbar)
        
        self.action_compilar = QAction(QIcon(os.path.join(icons_path, "compilar.png")), "Compilar", self)
        self.action_compilar.triggered.connect(self.disparar_compilacao)
        toolbar.addAction(self.action_compilar)
        
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
        
        self.port = QComboBox() 
        self.atualizar_lista_portas()
        toolbar.addWidget(self.port)

        self.btn_refresh_ports = QPushButton("↻")
        self.btn_refresh_ports.setFixedSize(30, 30)
        self.btn_refresh_ports.setToolTip("Atualizar Portas")
        self.btn_refresh_ports.clicked.connect(self.atualizar_lista_portas)
        toolbar.addWidget(self.btn_refresh_ports)

    def _create_central(self):
        self.editor_tabs = QTabWidget()
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.tabCloseRequested.connect(self._fechar_aba)

        editor = WandiCodeLinhas() 
        editor.setFont(QFont("Consolas", 12))
        editor.setPlainText("def setup():\n    pass\n\ndef loop():\n    pass")

        editor.textChanged.connect(self.marcar_como_modificado)
        
        self.editor_tabs.addTab(editor, "Código Wandi")
        self.setCentralWidget(self.editor_tabs)
        self.highlighter = WandiHighlighter(editor.document())

    def _fechar_aba(self, index):
        if self.editor_tabs.count() <= 1:
            self.statusBar().showMessage("Não é possível fechar a última aba de código.")
            return
        self.editor_tabs.removeTab(index)
        self.statusBar().showMessage("Aba removida.")

    def _create_console_dock(self):
        self.console_dock = QDockWidget("Mensageiro", self)
        self.console_tabs = QTabWidget() 
        
        style_flat = """
            QTabWidget::pane { border: none; }
            QPushButton#btnLimpar { background-color: transparent; color: #888888; border: none; padding: 0px 10px; font-size: 11px; font-weight: bold; }
            QPushButton#btnLimpar:hover { color: #ffffff; }
            QLineEdit { background-color: #2d2d2d; color: #ffffff; border: none; padding: 4px; }
            QTextEdit { background-color: #1e1e1e; border: none; color: #d4d4d4; }
        """
        self.console_tabs.setStyleSheet(style_flat)

        self.output_widget = QTextEdit()
        self.output_widget.setReadOnly(True)
        self.console_tabs.addTab(self.output_widget, "Output")

        serial_tab = QWidget()
        ser_layout = QVBoxLayout(serial_tab)
        ser_layout.setContentsMargins(0, 5, 0, 0)
        
        input_container = QHBoxLayout()
        self.btn_conectar_serial = QPushButton()
        self._atualizar_ui_serial_desconectado() # Define estado inicial do botão
        self.btn_conectar_serial.clicked.connect(self.alternar_conexao_serial)
        
        self.serial_input = QLineEdit()
        self.serial_input.setPlaceholderText("Enviar comando...")
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

        btn_limpar_geral = QPushButton("LIMPAR")
        btn_limpar_geral.setObjectName("btnLimpar")
        btn_limpar_geral.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_limpar_geral.clicked.connect(self._limpar_aba_atual)
        self.console_tabs.setCornerWidget(btn_limpar_geral, Qt.Corner.TopRightCorner)

        self.console_dock.setWidget(self.console_tabs)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.console_dock)

    def _limpar_aba_atual(self):
        index = self.console_tabs.currentIndex()
        if index == 0: self.output_widget.clear()
        elif index == 1: self.serial_widget.clear()

    def _create_project_dock(self):
        self.project_dock = QDockWidget("Simulação 3D", self)
        self.project_stack = QStackedWidget()
        
        self.simulation_view = QWebEngineView()
        
        # --- INICIALIZAÇÃO DA PONTE VIA WEBSOCKET ---
        # Note que não precisamos mais do QWebChannel para o Vercel
        self.web_bridge = WandiBridge(self) 
        # --------------------------------------------

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
        largura = 800 if index == 0 else 350
        self.resizeDocks([self.project_dock], [largura], Qt.Orientation.Horizontal)

    def _adjust_initial_layout(self):
        self.resizeDocks([self.console_dock], [220], Qt.Orientation.Vertical)
        self.resizeDocks([self.project_dock], [500], Qt.Orientation.Horizontal)

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

    def _create_statusbar(self):
        self.statusBar().showMessage("Pronto")

    # Garante o encerramento seguro de threads de hardware ao fechar a janela
    def closeEvent(self, event):
        if self.thread_serial and self.thread_serial.isRunning():
            self.thread_serial.parar()
            self.thread_serial.wait() # Aguarda a thread morrer antes de destruir a GUI
        super().closeEvent(event)


def load_style(app):
    try:
        if os.path.exists("style/dark.qss"):
            with open("style/dark.qss", "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
    except Exception as e: 
        print(f"Erro ao carregar estilo: {e}")

if __name__ == "__main__":
    # 1. Desativa a aceleração de hardware e silencia logs do motor Chromium
    # --disable-gpu: Mata o erro do IDCompositionDevice4 na raiz
    # --log-level=3: Garante que apenas erros fatais apareçam no terminal
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --log-level=3 --disable-software-rasterizer"

    # 2. Suas configurações anteriores (ajuda na estabilidade do Qt)
    os.environ["QT_LOGGING_RULES"] = "qt.webenginecontext.debug=false"
    os.environ["QT_D3D_CHECK_DEVICE_COMPATIBILITY"] = "0"

    app = QApplication(sys.argv)
    
    # Opcional: Se o erro persistir, descomente a linha abaixo para forçar renderização via Software
    # app.setAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL)

    window = WandiIDE()
    app.setFont(QFont("Consolas", 14))
    load_style(app)
    window.showMaximized()
    sys.exit(app.exec())