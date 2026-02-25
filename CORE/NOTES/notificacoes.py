from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame, QLabel, QProgressBar, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve

class WandiNotificacao(QWidget):
    """Card fixo de status (Versão Clássica)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.frame = QFrame(self)
        self.frame.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border: 1px solid #0078d4;
                border-radius: 8px;
            }
            QLabel#titulo {
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                background: transparent;
                border: none;
            }
            QLabel#status {
                color: #cccccc;
                font-size: 11px;
                background: transparent;
                border: none;
            }
        """)
        
        frame_layout = QVBoxLayout(self.frame)
        self.lbl_titulo = QLabel("Wandi Engine")
        self.lbl_titulo.setObjectName("titulo")
        
        self.lbl_status = QLabel("Iniciando verificação do sistema...")
        self.lbl_status.setObjectName("status")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setTextFormat(Qt.TextFormat.RichText)
        
        frame_layout.addWidget(self.lbl_titulo)
        frame_layout.addWidget(self.lbl_status)
        self.layout.addWidget(self.frame)
        self.setFixedSize(350, 100)

    def atualizar_status(self, texto):
        texto_limpo = texto.replace("<br>", "", 1).strip()
        self.lbl_status.setText(texto_limpo)

    def reposicionar(self, parent_widget):
        if parent_widget:
            x = parent_widget.width() - self.width() - 30
            y = parent_widget.height() - self.height() - 30
            self.move(x, y)


class WandiToast(QFrame):
    """Notificação flutuante empilhável com ANIMAÇÃO DE ENTRADA"""
    def __init__(self, parent, texto):
        super().__init__(parent)
        self.setFixedSize(380, 75)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose) 
        
        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #333;
                border-radius: 4px;
            }
            QLabel {
                color: #d4d4d4;
                font-size: 12px;
                border: none;
                background: transparent;
            }
            QProgressBar {
                border: none;
                background-color: #2d2d2d;
                height: 3px;
                border-radius: 1px;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
            }
        """)

        # --- Lógica de Animação de Entrada ---
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(600) # 0.5 segundos de fade-in
        self.anim.setStartValue(0)
        self.anim.setEndValue(20)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        # -------------------------------------

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        self.label = QLabel(texto.replace("<br>", "").strip())
        self.label.setTextFormat(Qt.TextFormat.RichText)
        self.label.setWordWrap(True)
        
        self.progress = QProgressBar()
        self.progress.setRange(0, 0) 
        self.progress.setFixedHeight(3)

        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(self.progress)
        
        self.show()
        self.anim.start() # Inicia o fade-in ao mostrar

    def set_texto(self, texto):
        self.label.setText(texto.strip())