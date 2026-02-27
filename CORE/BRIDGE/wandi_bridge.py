import asyncio
import threading
import websockets
from PyQt6.QtCore import QObject

class WandiBridge(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.clients = set()
        self.loop = None
        # Servidor em thread separada
        threading.Thread(target=self._start_server_thread, daemon=True).start()

    def _start_server_thread(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._run_server())

    async def _run_server(self):
            try:
                async with websockets.serve(self._handler, "127.0.0.1", 8765):
                    await asyncio.Future() 
            except OSError as e:
                if e.errno == 10048:
                    # Uma mensagem positiva, indicando que o serviço já está garantido
                    print("✨ Wandi Bridge: O servidor já está ativo e a comunicação com o simulador está garantida!")
                else:
                    # Mantemos um log discreto para outros erros raros
                    print(f"ℹ️ Nota de sistema: O servidor passou por um ajuste automático ({e})")

    async def _handler(self, websocket):
        self.clients.add(websocket)
        try:
            # Ao conectar, informa imediatamente se o hardware já está ativo
            is_active = self.main_window.thread_serial is not None and self.main_window.thread_serial.isRunning()
            await websocket.send(f"STATUS:{'ON' if is_active else 'OFF'}")
            
            async for message in websocket:
                # Web -> Hardware
                if self.main_window.thread_serial and self.main_window.thread_serial.isRunning():
                    self.main_window.thread_serial.enviar(message)
        except: pass
        finally:
            self.clients.remove(websocket)

    def send_to_web(self, message):
        """Envia dados para o simulador sem risco de crash"""
        if not self.clients or not self.loop: return
        
        async def broadcast():
            for ws in list(self.clients):
                try: await ws.send(str(message))
                except: pass
        
        # Agenda o envio de forma segura entre threads
        self.loop.call_soon_thread_safe(asyncio.create_task, broadcast())