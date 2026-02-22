import os
import random
from pathlib import Path
from PyQt6.QtWidgets import QMenu, QMessageBox, QFileDialog, QPlainTextEdit
from PyQt6.QtGui import QAction, QKeySequence, QFont

# No topo do arquivo wandimenu.py, importe o seu widget customizado
from CORE.LINHAS.linhas import WandiCodeLinhas
from highlighter import WandiHighlighter

class WandiMenu:
    def __init__(self, parent):
        self.parent = parent
        # Diretório realista
        self.default_dir = os.path.join(Path.home(), "Documents", "Wandi Studio", "Wandicode")
        os.makedirs(self.default_dir, exist_ok=True)
        
        self._setup_menu_backend()

    def _setup_menu_backend(self):
        menubar = self.parent.menuBar()
        menubar.clear() 

        # --- FICHEIRO ---
        self.file_menu = menubar.addMenu("Ficheiro")
        self._add_action(self.file_menu, "Novo", self._novo_arquivo).setShortcut(QKeySequence("Ctrl+N"))
        self._add_action(self.file_menu, "Abrir", self._abrir_arquivo).setShortcut(QKeySequence("Ctrl+O"))
        self.file_menu.addSeparator()
        self._add_action(self.file_menu, "Guardar", self._guardar_arquivo).setShortcut(QKeySequence("Ctrl+S"))
        self._add_action(self.file_menu, "Guardar Como", self._guardar_como).setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.file_menu.addSeparator()
        self._add_action(self.file_menu, "Sair", self.parent.close)

        # --- EDITAR ---
        self.edit_menu = menubar.addMenu("Editar")
        self._add_action(self.edit_menu, "Desfazer", self._undo_action).setShortcut(QKeySequence(QKeySequence.StandardKey.Undo))
        self._add_action(self.edit_menu, "Refazer", self._redo_action).setShortcut(QKeySequence(QKeySequence.StandardKey.Redo))
        self.edit_menu.addSeparator()
        self._add_action(self.edit_menu, "Copiar", self._copy_action).setShortcut(QKeySequence(QKeySequence.StandardKey.Copy))
        self._add_action(self.edit_menu, "Colar", self._paste_action).setShortcut(QKeySequence(QKeySequence.StandardKey.Paste))
        self._add_action(self.edit_menu, "Cortar", self._cut_action).setShortcut(QKeySequence(QKeySequence.StandardKey.Cut))
        self._add_action(self.edit_menu, "Selecionar tudo", self._select_all_action).setShortcut(QKeySequence(QKeySequence.StandardKey.SelectAll))

        # --- WANDI (RESTAURADO COMPLETO) ---
        self.wandi_menu = menubar.addMenu("Wandi")
        self._add_action(self.wandi_menu, "Mensageiro", lambda: self.parent.console_dock.show())
        self._add_action(self.wandi_menu, "Wandi Vision", self._placeholder_enviar)
        self._add_action(self.wandi_menu, "Wandi Chatbot", self._placeholder_enviar)
        self.wandi_menu.addSeparator()
        self._add_action(self.wandi_menu, "Compilar", self.parent.disparar_compilacao).setShortcut(QKeySequence("F5"))
        self._add_action(self.wandi_menu, "Enviar", self._placeholder_enviar)
        self.wandi_menu.addSeparator()
        self._add_action(self.wandi_menu, "3D", lambda: self.parent._switch_view(0, "Simulação 3D"))
        self._add_action(self.wandi_menu, "Biblioteca", lambda: self.parent._switch_view(1, "Biblioteca"))

        # --- MAIS ---
        self.mais_menu = menubar.addMenu("Mais")
        self._add_action(self.mais_menu, "Wandi Robot", self._sobre_wandi)
        self.mais_menu.addSeparator()
        self._add_action(self.mais_menu, "Sobre Wandi IDE", self._sobre_wandi)
        self._add_action(self.mais_menu, "Website Causa-Efeito", self._sobre_wandi)
        self.mais_menu.addSeparator()
        self._add_action(self.mais_menu, "Documentacao", self._sobre_wandi)
        self._add_action(self.mais_menu, "Manual", self._sobre_wandi)

    # --- LÓGICA DE ABAS E SALVAMENTO ---

    def _novo_arquivo(self):
        """Cria uma nova aba usando o editor customizado da Wandi IDE"""
        # Usar o seu widget que contém a lógica de linhas
        novo_editor = WandiCodeLinhas() 
        novo_editor.setFont(QFont("Consolas", 13))
        
        # Aplica o Highlighter na nova aba
        self.parent.highlighter = WandiHighlighter(novo_editor.document())
        
        codigo_inicial = "def setup():\n    pass\n\ndef loop():\n    pass"
        novo_editor.setPlainText(codigo_inicial)
        
        idx = self.parent.editor_tabs.addTab(novo_editor, "novo_projeto.py")
        self.parent.editor_tabs.setCurrentIndex(idx)
        self.parent.statusBar().showMessage("Novo ficheiro criado com sucesso.")

    def _guardar_arquivo(self):
        editor = self.parent.editor_tabs.currentWidget()
        if not editor: return
        
        nome_atual = self.parent.editor_tabs.tabText(self.parent.editor_tabs.currentIndex())
        
        # Se ainda for o nome padrão, gera o nome aleatório ou pede "Guardar Como"
        if "novo_projeto" in nome_atual or "Código Wandi" in nome_atual:
            sufixo = random.randint(100, 999)
            nome_arquivo = f"wandicode{sufixo}.py"
            caminho_completo = os.path.join(self.default_dir, nome_arquivo)
        else:
            caminho_completo = os.path.join(self.default_dir, nome_atual)

        try:
            with open(caminho_completo, "w", encoding="utf-8") as f:
                f.write(editor.toPlainText())
            self.parent.editor_tabs.setTabText(self.parent.editor_tabs.currentIndex(), os.path.basename(caminho_completo))
            self.parent.statusBar().showMessage(f"Guardado: {caminho_completo}")
        except Exception as e:
            self.parent.log_to_output(f"Erro ao salvar: {e}")

    def _guardar_como(self):
        caminho, _ = QFileDialog.getSaveFileName(self.parent, "Guardar Como", self.default_dir, "Python Files (*.py)")
        if caminho:
            try:
                editor = self.parent.editor_tabs.currentWidget()
                if editor:
                    with open(caminho, "w", encoding="utf-8") as f:
                        f.write(editor.toPlainText())
                    self.parent.editor_tabs.setTabText(self.parent.editor_tabs.currentIndex(), os.path.basename(caminho))
                    self.parent.statusBar().showMessage(f"Salvo em: {caminho}")
            except Exception as e:
                QMessageBox.critical(self.parent, "Erro", f"Erro ao guardar: {e}")

    # --- APOIO ---
    def _add_action(self, menu, text, func):
        action = QAction(text, self.parent)
        action.triggered.connect(func)
        menu.addAction(action)
        return action

    def _abrir_arquivo(self):
        caminho, _ = QFileDialog.getOpenFileName(self.parent, "Abrir Código", self.default_dir, "Python Files (*.py)")
        if caminho:
            try:
                with open(caminho, "r", encoding="utf-8") as f:
                    self.parent.editor_tabs.currentWidget().setPlainText(f.read())
                self.parent.editor_tabs.setTabText(self.parent.editor_tabs.currentIndex(), os.path.basename(caminho))
            except Exception as e:
                QMessageBox.critical(self.parent, "Erro", f"Erro ao abrir: {e}")

    def _placeholder_enviar(self):
        self.parent.console_dock.show()
        self.parent.statusBar().showMessage("Enviando para a placa...")

    # --- EDIÇÃO ---
    def _undo_action(self): 
        if self.parent.editor_tabs.currentWidget(): self.parent.editor_tabs.currentWidget().undo()
    def _redo_action(self): 
        if self.parent.editor_tabs.currentWidget(): self.parent.editor_tabs.currentWidget().redo()
    def _copy_action(self): 
        if self.parent.editor_tabs.currentWidget(): self.parent.editor_tabs.currentWidget().copy()
    def _paste_action(self): 
        if self.parent.editor_tabs.currentWidget(): self.parent.editor_tabs.currentWidget().paste()
    def _cut_action(self): 
        if self.parent.editor_tabs.currentWidget(): self.parent.editor_tabs.currentWidget().cut()
    def _select_all_action(self): 
        if self.parent.editor_tabs.currentWidget(): self.parent.editor_tabs.currentWidget().selectAll()
    def _sobre_wandi(self): QMessageBox.about(self.parent, "Sobre", "Wandi Studio IDE - Sistema Integrado De Ensino De Robotica")