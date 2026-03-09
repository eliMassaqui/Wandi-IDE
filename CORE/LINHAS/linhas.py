from PyQt6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PyQt6.QtGui import QPainter, QColor, QTextFormat, QFont
from PyQt6.QtCore import QRect, QSize, Qt

class LineNumberArea(QWidget):
    """Área lateral responsável pelo desenho dos números."""
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)

class WandiCodeLinhas(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        
        # Conexões de sinal para atualização automática
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        
        # Configuração de Fonte (Consolas, 14px)
        font = QFont("Consolas", 14)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        
        self.update_line_number_area_width(0)
        self.highlight_current_line()
        
        # Estilo padrão escuro Wandi Studio
        self.setStyleSheet("""
            QPlainTextEdit {
                border: none; 
                background-color: #1e1e1e; 
                color: #d4d4d4;
            }
        """)

    def line_number_area_width(self):
        """Calcula a largura da calha baseado na quantidade de dígitos."""
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value /= 10
            digits += 1
        
        # 20px de respiro + largura do caractere '9' vezes o número de dígitos
        space = 20 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def highlight_current_line(self):
        """Destaque visual da linha ativa."""
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor("#2c2c2c"))
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def wheelEvent(self, event):
        """Implementação de Zoom: Ctrl + Roda do mouse."""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoomIn(1)
            else:
                self.zoomOut(1)
        else:
            super().wheelEvent(event)

    def lineNumberAreaPaintEvent(self, event):
        """Pintura customizada dos números acompanhando a métrica da fonte."""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#1e1e1e")) # Fundo da calha

        # Sincroniza a fonte do painter com o editor (14px Consolas)
        painter.setFont(self.font())

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                
                # Cor azul para linha atual, cinza para as demais
                is_current = self.textCursor().blockNumber() == block_number
                painter.setPen(QColor("#007acc") if is_current else QColor("#c1c1c1c1"))
                
                # Desenha o texto alinhado à direita com padding de 8px
                painter.drawText(0, top, self.line_number_area.width() - 8, 
                                 self.fontMetrics().height(),
                                 Qt.AlignmentFlag.AlignRight, number)
            
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1