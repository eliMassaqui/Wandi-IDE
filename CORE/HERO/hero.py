import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsDropShadowEffect, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QPixmap, QFont, QColor, QPainter, QPainterPath, QPen

class WandiHeroSide(QWidget):
    start_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)

        # --- ESTILO DE FUNDO ---
        self.setStyleSheet("""
            WandiHeroSide {
                background-color: #f5f7fa; 
                border-left: 1px solid #e1e4e8;
            }
        """)

        # --- ÍCONE CIRCULAR ---
        # Ajustado para 200x200 para um encaixe mais justo
        self.container_icon = QFrame()
        self.container_icon.setFixedSize(200, 200) 
        self.container_icon.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.icon_label = QLabel(self.container_icon)
        self.icon_label.setFixedSize(180, 180)
        # Centraliza a label de 180 dentro do container de 200 (margem de 10px)
        self.icon_label.move(10, 10) 
        
        # Caminho do ícone
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_icon_path = os.path.abspath(os.path.join(current_dir, "..", "..", "icons", "wandi.png"))
        self._set_circular_img(base_icon_path)
        
        # --- TÍTULO ---
        self.title = QLabel("Wandi Studio")
        font_title = QFont("Segoe UI", 32, QFont.Weight.Bold)
        self.title.setFont(font_title)
        self.title.setStyleSheet("color: #1a1d21; background: transparent; letter-spacing: 1px;")
        
        # --- SUBTÍTULO ---
        self.subtitle = QLabel("WANDI IDE - Ambiente de desenvolvimento integrado de robótica")
        # Ajustado para 14pt (35pt era muito grande para o layout subir bem)
        font_sub = QFont("Segoe UI", 14)
        self.subtitle.setFont(font_sub)
        # Cor alterada para cinza escuro para visibilidade no fundo claro
        self.subtitle.setStyleSheet("color: #5f6368; background: transparent;")

        # --- BOTÃO DE AÇÃO ---
        self.btn_action = QLabel("INICIAR SIMULAÇÃO")
        self.btn_action.setFont(QFont("Roboto", 10, QFont.Weight.Bold))
        self.btn_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_action.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_action.setFixedSize(180, 40)
        
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
        
        shadow_btn = QGraphicsDropShadowEffect()
        shadow_btn.setBlurRadius(15)
        shadow_btn.setColor(QColor(0, 0, 0, 50))
        shadow_btn.setOffset(0, 4)
        self.btn_action.setGraphicsEffect(shadow_btn)

        # --- MONTAGEM DO LAYOUT (EFEITO "PARA CIMA") ---
        # O stretch de baixo (2) é maior que o de cima (1), empurrando o conteúdo para o topo
        layout.addStretch(1) 
        layout.addWidget(self.container_icon, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(5) 
        layout.addWidget(self.title, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.subtitle, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(30) 
        layout.addWidget(self.btn_action, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(2) 

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
        """Desenha a linha neon com encaixe perfeito no contorno da imagem."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Geometria dinâmica baseada no container
        rect = self.container_icon.geometry()
        center = rect.center()
        
        # O raio da imagem é 90 (180/2). 
        # Usamos 91 para a linha neon ficar exatamente no limite externo da imagem.
        radius = 91

        # 1. Brilho (Glow) Externo
        pen_glow = QPen(QColor(0, 120, 212, 50)) 
        pen_glow.setWidth(10)
        painter.setPen(pen_glow)
        painter.drawEllipse(center, radius + 2, radius + 2)

        # 2. Linha Neon Central
        pen_neon = QPen(QColor(0, 162, 255)) 
        pen_neon.setWidth(3)
        painter.setPen(pen_neon)
        painter.drawEllipse(center, radius, radius)

    def mousePressEvent(self, event):
        """Detecta clique no botão ou no container do ícone."""
        if self.btn_action.geometry().contains(event.pos()) or \
           self.container_icon.geometry().contains(event.pos()):
            self.start_requested.emit()