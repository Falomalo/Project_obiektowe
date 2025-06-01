from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
import os
import folium

class MapWidget(QWebEngineView):
    def __init__(self, x_pos=None, y_pos=None, x_len=None, y_len=None, parent=None):
        super().__init__(parent)
        
        if all(v is not None for v in [x_pos, y_pos, x_len, y_len]):
            self.setGeometry(x_pos, y_pos, x_len, y_len)
        
        self.__load_map()

    def __load_map(self):
        map_path = os.path.abspath("resources/map.html")
        self.setUrl(QUrl.fromLocalFile(map_path))
        self.page().runJavaScript("pyjs = {}; pyjs.handleClick = function(lat, lng) {};")

    def update_map(self):
        self.__save_and_reload_map()

    def add_marker(self, lat, lng):
        try:
            folium.Marker([lat, lng], popup=f"Marker at ({lat}, {lng})").add_to(self.__map)
            self.update_map()
        except ValueError:
            print("Invalid coordinates")

    def __save_and_reload_map(self):
        self.__map.save("resources/map.html")
        self.setUrl(QUrl.fromLocalFile(os.path.abspath("resources/map.html")))
