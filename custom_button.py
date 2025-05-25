from functools import partial
from widgets.base_button import BaseButton

class CustomButton(BaseButton):
    def __init__(self, text, x_pos, y_pos, x_len, y_len, callback=None, parent=None):
        super().__init__(text, x_pos, y_pos, x_len, y_len, callback, parent)

class GraphButton(CustomButton):
    def __init__(self, x_pos, y_pos, x_len, y_len, func, parent=None):
        super().__init__("Wykres", x_pos, y_pos, x_len, y_len, func, parent)

class MapButton(CustomButton):
    def __init__(self, x_pos, y_pos, x_len, y_len, func, parent=None):
        super().__init__("Mapa", x_pos, y_pos, x_len, y_len, func, parent)
