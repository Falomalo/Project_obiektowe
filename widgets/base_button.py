from PyQt5.QtWidgets import QPushButton

class BaseButton(QPushButton):
    def __init__(self, text, x_pos, y_pos, x_len, y_len, callback=None, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setGeometry(x_pos, y_pos, x_len, y_len)
        
        if callback:
            self.clicked.connect(callback)
