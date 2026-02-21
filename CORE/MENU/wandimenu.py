from PyQt6.QtWidgets import QMenu, QMessageBox
from PyQt6.QtGui import QAction

class WandiMenu:
    def __init__(self, parent):
        self.parent = parent
        self._setup_menu_backend()

    def _setup_menu_backend(self):
        menubar = self.parent.menuBar()
        menubar.clear() 

        # --- FICHEIRO ---
        self.file_menu = menubar.addMenu("Ficheiro")
        self._add_action(self.file_menu, "Novo", self._placeholder, "Novo arquivo")
        self._add_action(self.file_menu, "Abrir", self._placeholder, "Abrir arquivo")
        self._add_action(self.file_menu, "Abrir recente", self._placeholder, "Abrir arquivo")
        self._add_action(self.file_menu, "Guardar", self._placeholder, "Projeto guardado")
        self._add_action(self.file_menu, "Guardar Como", self._placeholder, "Projeto guardado como:")
        self.file_menu.addSeparator()
        self._add_action(self.file_menu, "Sair", self.parent.close)

        # --- EDITAR ---
        self.edit_menu = menubar.addMenu("Editar")
        self._add_action(self.edit_menu, "Desfazer", self._undo_action)
        self._add_action(self.edit_menu, "Refazer", self._redo_action)
        self._add_action(self.edit_menu, "Copiar", self._redo_action)
        self._add_action(self.edit_menu, "Colar", self._redo_action)
        self._add_action(self.edit_menu, "Cortar", self._redo_action)
        self._add_action(self.edit_menu, "Selecionar tudo", self._redo_action)

        # --- WANDI ---
        self.wandi_menu = menubar.addMenu("Wandi")
        self._add_action(self.wandi_menu, "Mensageiro", self._compilar_logic)
        self._add_action(self.wandi_menu, "Wandi Vision", self._enviar_logic)
        self._add_action(self.wandi_menu, "Wandi Chatbot", self._enviar_logic)
        self.wandi_menu.addSeparator()
        self._add_action(self.wandi_menu, "Compilar", self._compilar_logic)
        self._add_action(self.wandi_menu, "Enviar", self._enviar_logic)
        self.wandi_menu.addSeparator()
        self._add_action(self.wandi_menu, "3D", self._enviar_logic)
        self._add_action(self.wandi_menu, "Biblioteca", self._enviar_logic)

        # --- MAIS ---
        self.mais_menu = menubar.addMenu("Mais")
        self._add_action(self.mais_menu, "Wandi Robot", self._sobre_wandi)
        self.mais_menu.addSeparator()
        self._add_action(self.mais_menu, "Sobre Wandi IDE", self._sobre_wandi)
        self._add_action(self.mais_menu, "Website Causa-Efeito", self._sobre_wandi)
        self.mais_menu.addSeparator()
        self._add_action(self.mais_menu, "Documentacao", self._sobre_wandi)
        self._add_action(self.mais_menu, "Manual", self._sobre_wandi)

    def _add_action(self, menu, text, func, arg=None):
        action = QAction(text, self.parent)
        if arg:
            action.triggered.connect(lambda: func(arg))
        else:
            action.triggered.connect(func)
        menu.addAction(action)
        return action

    def _placeholder(self, msg):
        self.parent.statusBar().showMessage(msg)

    def _undo_action(self):
        current = self.parent.editor_tabs.currentWidget()
        if current: current.undo()

    def _redo_action(self):
        current = self.parent.editor_tabs.currentWidget()
        if current: current.redo()

    def _compilar_logic(self):
        self.parent.console_dock.show()
        self.parent.statusBar().showMessage("Compilando...")

    def _enviar_logic(self):
        self.parent.console_dock.show()
        self.parent.statusBar().showMessage("Enviando...")

    def _sobre_wandi(self):
        QMessageBox.about(self.parent, "Sobre", "Wandi Studio IDE - Sistema Integrado De Ensino De Robotica")