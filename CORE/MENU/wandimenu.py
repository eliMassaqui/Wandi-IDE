import os
import random
from pathlib import Path
from PyQt6.QtWidgets import QMenu, QMessageBox, QFileDialog, QPlainTextEdit
from PyQt6.QtGui import QAction, QKeySequence, QFont

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
        
        # Guardar (Ctrl+S salva direto com nome aleatório)
        btn_guardar = self._add_action(self.file_menu, "Guardar", self._guardar_arquivo)
        btn_guardar.setShortcut(QKeySequence("Ctrl+S"))
        
        # Guardar Como (Pede nome ao usuário)
        btn_guardar_como = self._add_action(self.file_menu, "Guardar Como", self._guardar_como)
        btn_guardar_como.setShortcut(QKeySequence("Ctrl+Shift+S"))
        
        self.file_menu.addSeparator()
        self._add_action(self.file_menu, "Sair", self.parent.close)

        # --- EDITAR (Shortcuts corrigidos para PyQt6) ---
        self.edit_menu = menubar.addMenu("Editar")
        self._add_action(self.edit_menu, "Desfazer", self._undo_action).setShortcut(QKeySequence(QKeySequence.StandardKey.Undo))
        self._add_action(self.edit_menu, "Refazer", self._redo_action).setShortcut(QKeySequence(QKeySequence.StandardKey.Redo))
        self.edit_menu.addSeparator()
        self._add_action(self.edit_menu, "Copiar", self._copy_action).setShortcut(QKeySequence(QKeySequence.StandardKey.Copy))
        self._add_action(self.edit_menu, "Colar", self._paste_action).setShortcut(QKeySequence(QKeySequence.StandardKey.Paste))
        self._add_action(self.edit_menu, "Cortar", self._cut_action).setShortcut(QKeySequence(QKeySequence.StandardKey.Cut))
        self._add_action(self.edit_menu, "Selecionar tudo", self._select_all_action).setShortcut(QKeySequence(QKeySequence.StandardKey.SelectAll))

        # --- RESTANTE DOS MENUS ---
        self.wandi_menu = menubar.addMenu("Wandi")
        self._add_action(self.wandi_menu, "Compilar", self.parent.disparar_compilacao).setShortcut(QKeySequence("F5"))
        self.mais_menu = menubar.addMenu("Mais")
        self._add_action(self.mais_menu, "Sobre Wandi IDE", self._sobre_wandi)

    # --- LÓGICA DE ABAS E SALVAMENTO ---

    def _novo_arquivo(self):
        """Cria uma nova aba com o código inicial padrão"""
        novo_editor = QPlainTextEdit()
        
        # Mantém a fonte original (Consolas) para lucidez visual
        novo_editor.setFont(QFont("Consolas", 13))
        
        # Define o código inicial (Lógica original)
        codigo_inicial = "def setup():\n    pass\n\ndef loop():\n    pass"
        novo_editor.setPlainText(codigo_inicial)
        
        # Adiciona a aba e foca nela
        idx = self.parent.editor_tabs.addTab(novo_editor, "novo_projeto.py")
        self.parent.editor_tabs.setCurrentIndex(idx)
        self.parent.statusBar().showMessage("Novo ficheiro criado com sucesso.")

    def _guardar_arquivo(self):
        """Salva direto com nome wandicodeXXX.py"""
        try:
            editor = self.parent.editor_tabs.currentWidget()
            if not editor: return

            sufixo = random.randint(100, 999)
            nome_arquivo = f"wandicode{sufixo}.py"
            caminho_completo = os.path.join(self.default_dir, nome_arquivo)

            with open(caminho_completo, "w", encoding="utf-8") as f:
                f.write(editor.toPlainText())

            self.parent.editor_tabs.setTabText(self.parent.editor_tabs.currentIndex(), nome_arquivo)
            self.parent.statusBar().showMessage(f"Projeto guardado em: {nome_arquivo}")
        except Exception as e:
            self.parent.statusBar().showMessage(f"Erro ao guardar: {e}")

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
    def _sobre_wandi(self): QMessageBox.about(self.parent, "Sobre", "Wandi Studio IDE")