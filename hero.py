import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsDropShadowEffect, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QPixmap, QFont, QColor, QPainter, QPainterPath, QPen, QBrush

class WandiHeroSide(QWidget):
    start_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Layout principal centralizado
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)

        # --- ESTILO DE FUNDO (PROFISSIONAL/CLARO) ---
        # Usamos uma cor base clara com uma borda sutil de separação
        self.setStyleSheet("""
            WandiHeroSide {
                background-color: #f5f7fa; /* Cinza Tech muito claro */
                border-left: 1px solid #e1e4e8;
            }
        """)

        # --- ÍCONE CIRCULAR WANDI COM LINHA NEON (DESENHADO NO PAINTEVENT) ---
        self.container_icon = QFrame()
        self.container_icon.setFixedSize(220, 220) # Espaço para o círculo + linha brilhante
        self.container_icon.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Label interna que segura a imagem wandi.png
        self.icon_label = QLabel(self.container_icon)
        self.icon_label.setFixedSize(180, 180)
        # Centraliza a label dentro do container
        self.icon_label.move(20, 20) 
        
        caminho_icone = os.path.join(os.path.dirname(__file__), "icons", "wandi.png")
        self._set_circular_img(caminho_icone)
        
        # --- TÍTULO (Estilo Google Font Roboto/Segoe) ---
        self.title = QLabel("Wandi Studio")
        # Usamos Segoe UI (padrão Windows moderno) ou Arial como fallback
        font_title = QFont("Segoe UI", 32, QFont.Weight.Bold)
        self.title.setFont(font_title)
        self.title.setStyleSheet("color: #1a1d21; background: transparent; letter-spacing: 1px;")
        
        # --- SUBTÍTULO ---
        self.subtitle = QLabel("WANDI IDE - Ambiente de desenvolvimento integrado de robótica")
        font_sub = QFont("Segoe UI", 11)
        self.subtitle.setFont(font_sub)
        self.subtitle.setStyleSheet("color: #586069; background: transparent;")

        # --- BOTÃO DE AÇÃO (Simulando Google Material Design) ---
        self.btn_action = QLabel("INICIAR SIMULAÇÃO")
        self.btn_action.setFont(QFont("Roboto", 10, QFont.Weight.Bold))
        self.btn_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_action.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_action.setFixedSize(180, 40)
        
        # Estilo do botão: Azul Wandi, cantos arredondados, sombra leve
        self.btn_action.setStyleSheet("""
            QLabel {
                background-color: #0078d4;
                color: white;
                border-radius: 20px;
                letter-spacing: 1px;
                border: none;
            }
            QLabel:hover {
                background-color: #005a9e;
            }
        """)
        
        # Sombra sutil no botão para profundidade (Material)
        shadow_btn = QGraphicsDropShadowEffect()
        shadow_btn.setBlurRadius(15)
        shadow_btn.setColor(QColor(0, 0, 0, 50))
        shadow_btn.setOffset(0, 4)
        self.btn_action.setGraphicsEffect(shadow_btn)

        # Montagem da estrutura
        layout.addStretch()
        layout.addWidget(self.container_icon, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(self.title, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.subtitle, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(30)
        layout.addWidget(self.btn_action, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

    def _set_circular_img(self, path):
        """Corta a imagem wandi.png em um círculo perfeito."""
        if os.path.exists(path):
            pix = QPixmap(path).scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            out = QPixmap(180, 180)
            out.fill(Qt.GlobalColor.transparent)
            painter = QPainter(out)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            path_c = QPainterPath()
            path_c.addEllipse(0, 0, 180, 180)
            painter.setClipPath(path_c)
            painter.drawPixmap(0, 0, pix)
            painter.end()
            self.icon_label.setPixmap(out)

    def paintEvent(self, event):
        """Desenha a linha azul brilhante em volta do círculo."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Encontrar o centro do container do ícone
        # Nota: container_icon.pos() é relativo ao layout, precisamos converter para relativo ao widget
        center = self.container_icon.geometry().center()
        radius = 95 # Um pouco maior que o raio da imagem (90)

        # 1. Desenhar o brilho (Glow) externo (linha grossa e suave)
        pen_glow = QPen(QColor(0, 120, 212, 60)) # Azul transparente
        pen_glow.setWidth(12)
        painter.setPen(pen_glow)
        painter.drawEllipse(center, radius, radius)

        # 2. Desenhar a linha neon central (linha fina e intensa)
        pen_neon = QPen(QColor(0, 162, 255)) # Azul brilhante
        pen_neon.setWidth(3)
        painter.setPen(pen_neon)
        painter.drawEllipse(center, radius, radius)

    def mousePressEvent(self, event):
        """Detecta clique no botão ou no container do ícone."""
        if self.btn_action.geometry().contains(event.pos()) or \
           self.container_icon.geometry().contains(event.pos()):
            self.start_requested.emit()