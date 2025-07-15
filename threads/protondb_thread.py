import json
from urllib.request import urlopen, Request
from PyQt5.QtCore import QThread, pyqtSignal

from config_manager import ConfigManager

class ProtonDBThread(QThread):
    """
    Hilo para obtener el estado de un juego desde la API de ProtonDB
    sin bloquear la interfaz de usuario.
    """
    db_status_ready = pyqtSignal(str, str)  

    def __init__(self, appid: str):
        super().__init__()
        self.appid = appid

    def run(self):
        """
        Este método se ejecuta en segundo plano.
        """
        rating = "Desconocido"
        try:
            url = f"https://www.protondb.com/api/v1/reports/summaries/{self.appid}.json"
            req = Request(url, headers={'User-Agent': 'WineProtonManager/1.0'})
            
            with urlopen(req, timeout=15) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read().decode())

                    rating = data.get("tier", "Sin datos")
                else:
                    rating = f"Error HTTP {response.getcode()}"
        except Exception:

            rating = "No encontrado"
        finally:

            self.db_status_ready.emit(self.appid, rating.capitalize())
