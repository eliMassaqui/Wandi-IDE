import os
import threading
import http.server
import socketserver
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView

class WandiHandler(http.server.SimpleHTTPRequestHandler):
    """
    Handler customizado para servir arquivos de um diretório específico
    sem precisar usar o os.chdir(), evitando interferir na IDE.
    """
    def __init__(self, *args, **kwargs):
        # O segredo está em passar o diretório explicitamente aqui
        super().__init__(*args, **kwargs)

class Wandi3DServer:
    def __init__(self, port=5173, directory="3D"):
        self.port = port
        self.directory = directory
        self.httpd = None

    def start(self):
        # 1. Localiza a pasta 3D sem mudar o diretório do sistema
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        ide_root = os.path.abspath(os.path.join(current_file_dir, "..", ".."))
        path_3d = os.path.join(ide_root, self.directory)

        if not os.path.exists(path_3d):
            print(f"⚠️ Erro: Pasta '{self.directory}' não encontrada em {path_3d}")
            return

        def run_server():
            # Criamos uma função lambda para passar o diretório ao Handler
            handler = lambda *args, **kwargs: http.server.SimpleHTTPRequestHandler(
                *args, directory=path_3d, **kwargs
            )
            
            socketserver.TCPServer.allow_reuse_address = True
            
            try:
                with socketserver.TCPServer(("", self.port), handler) as httpd:
                    self.httpd = httpd
                    print(f"🚀 Servidor 3D isolado em: {path_3d}")
                    httpd.serve_forever()
            except Exception as e:
                print(f"❌ Erro no servidor: {e}")

        threading.Thread(target=run_server, daemon=True).start()

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()

class Wandi3DWidget(QWebEngineView):
    def __init__(self, url=f"http://localhost:5173"):
        super().__init__()
        self.page().setBackgroundColor(Qt.GlobalColor.black)
        
        # Configurações de isolamento e performance
        settings = self.settings()
        settings.setAttribute(settings.WebAttribute.ShowScrollBars, False)
        settings.setAttribute(settings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(settings.WebAttribute.Accelerated2dCanvasEnabled, True)
        
        self.load(QUrl(url))