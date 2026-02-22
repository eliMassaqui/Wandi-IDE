import re
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import Qt

class WandiHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules = []

        # --- PALETA WANDI DEFINITIVA ---
        colors = {
            'blue_core':   "#4d94ff",  # Azul (setup, loop)
            'cyan_hw':     "#00f5ff",  # Ciano Vivo (Serial, pinMode, digitalWrite)
            'green_light':   "#00f6b8",  # Verde claro (Números/Pinos)
            'yellow_sys':  "#ffcc00",  # Amarelo (HIGH, LOW, INPUT, OUTPUT)
            'orange_wandi': "#F28C28", # Laranja solicitado (#F28C28)
            'purple_logic':"#c586c0",  # Roxo (def, if, else, return)
            'green_comm':  "#6a9955",  # Verde (Comentários)
        }

        # 1. Funções de Ciclo (Azul)
        self._add_rule([r'\bsetup\b', r'\bloop\b'], colors['blue_core'], bold=True)

        # 2. Hardware e Comunicação (Ciano Vivo)
        hw_cmds = ["Serial", "pinMode", "digitalWrite", "digitalRead", "analogWrite", 
                   "analogRead", "delay", "millis", "begin", "print", "println"]
        self._add_rule([rf'\b{cmd}\b' for cmd in hw_cmds], colors['cyan_hw'])

        # 3. Constantes de Estado (Amarelo)
        constants = ["HIGH", "LOW", "INPUT", "OUTPUT", "INPUT_PULLUP", "pass"]
        self._add_rule([rf'\b{c}\b' for c in constants], colors['yellow_sys'], bold=True)

        # 4. Lógica de Controle (Roxo)
        keywords = ["and", "break", "continue", "def", "elif", "else", "for", "if", "return", "while", "import"]
        self._add_rule([rf'\b{kw}\b' for kw in keywords], colors['purple_logic'])

        # 5. Números (Ciano Escuro solicitado)
        self.rules.append((re.compile(r'\b\d+\b'), self._format(colors['green_light'])))

        # 6. Strings (Laranja #F28C28)
        self.rules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), self._format(colors['orange_wandi'])))
        self.rules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), self._format(colors['orange_wandi'])))

        # 7. Comentários (Verde)
        self.rules.append((re.compile(r'#[^\n]*'), self._format(colors['green_comm'])))

    def _add_rule(self, patterns, color, bold=False):
        for pattern in patterns:
            self.rules.append((re.compile(pattern), self._format(color, bold)))

    def _format(self, color, bold=False):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold: fmt.setFontWeight(QFont.Weight.Bold)
        return fmt

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)