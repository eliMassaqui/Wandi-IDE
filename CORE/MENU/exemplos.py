import os
from PyQt6.QtGui import QAction

class WandiExemplos:
    def __init__(self, parent_menu, ide_parent):
        """
        parent_menu: O menu 'Wandi' onde os exemplos serão inseridos.
        ide_parent: A instância da WandiIDE para acessar os métodos de editor.
        """
        self.parent_menu = parent_menu
        self.ide_parent = ide_parent
        
        # Caminho base dos exemplos
        self.base_path = os.path.join(
            os.path.expanduser("~"), 
            "Documents", "Wandi Studio", "Wandicode", "Exemplos"
        )
        
        # Cria a pasta caso não exista
        os.makedirs(self.base_path, exist_ok=True)
        
        # Inicia a construção do menu de exemplos
        self.menu_exemplos = self.parent_menu.addMenu("Exemplos")
        self.atualizar_exemplos()

    def atualizar_exemplos(self):
        self.menu_exemplos.clear()
        
        # Lista as subpastas (Categorias)
        if not os.path.exists(self.base_path):
            return

        categorias = sorted([d for d in os.listdir(self.base_path) 
                            if os.path.isdir(os.path.join(self.base_path, d))])

        for cat in categorias:
            sub_menu = self.menu_exemplos.addMenu(cat)
            caminho_cat = os.path.join(self.base_path, cat)
            
            # Lista os arquivos .py dentro da categoria
            arquivos = sorted([f for f in os.listdir(caminho_cat) if f.endswith(".py")])
            
            if not arquivos:
                sub_menu.addAction("Vazio").setEnabled(False)
            
            for arq in arquivos:
                nome_exemplo = arq.replace(".py", "")
                caminho_completo = os.path.join(caminho_cat, arq)
                
                action = QAction(nome_exemplo, self.ide_parent)
                # O segredo: lambda com argumento padrão para capturar o caminho atual do loop
                action.triggered.connect(lambda chk, p=caminho_completo: self.carregar_exemplo(p))
                sub_menu.addAction(action)

    def carregar_exemplo(self, caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                conteudo = f.read()
            
            editor = self.ide_parent.editor_tabs.currentWidget()
            if editor:
                editor.setPlainText(conteudo)
                # Define como um novo arquivo não salvo (para evitar sobrescrever o exemplo original)
                self.ide_parent.current_file_path = None
                self.ide_parent.editor_tabs.setTabText(
                    self.ide_parent.editor_tabs.currentIndex(), 
                    f"Exemplo: {os.path.basename(caminho)}"
                )
                self.ide_parent.statusBar().showMessage(f"Exemplo carregado: {os.path.basename(caminho)}")
        except Exception as e:
            self.ide_parent.log_to_output(f"Erro ao carregar exemplo: {e}")