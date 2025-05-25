from functools import partial
from PyQt5.QtWidgets import QWidget, QPushButton

class ButtonsPanel(QWidget):
    def __init__(self, parent=None, callback=None):
        super().__init__(parent)
        self.__callback = callback
        self.__create_buttons()

    def __create_buttons(self):
        button_width = 75
        button_height = 30
        spacing = 10

        self.__buttons = [QPushButton(str(2013 + i), self) for i in range(10)]
        for i, button in enumerate(self.__buttons):
            button.setGeometry((button_width + spacing) * i, 0, button_width, button_height)
            button.clicked.connect(partial(self.__handle_button_click, 2013 + i))
            button.show()

    def __handle_button_click(self, year):
        print(f"Button for year {year} clicked")
        if self.__callback:
            self.__callback(year)
        else:
            print("Callback is not defined.")
