import sys
from PyQt5.QtGui import QFont, QPixmap, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QListWidget, QLineEdit, QListWidgetItem, QLabel
from data.countries import Countries
from data.voivodeships import Voivodeships
from data.eurostat import EurostatDataFetcher
from widgets.base_button import BaseButton
from widgets.map_widget import MapWidget
from widgets.buttons_panel import ButtonsPanel
from widgets.gengraph import GenGraph
from utils import Map
from utils import DataProcessor
class CountryFilter:
    def __init__(self, parent_widget, countries):
        self.__country_list = QListWidget(parent_widget)
        self.__search_bar = QLineEdit(parent_widget)
        self.specific_countries = set()
        self.__countries = countries

        self.__setup_ui()

    def __setup_ui(self):
        self.__country_list.setGeometry(1200, 300, 360, 400)
        self.__search_bar.setGeometry(1200, 200, 360, 50)
        self.__populate_country_list()
        self.__connect_signals()

    def __populate_country_list(self):
        for country in self.__countries.as_array():
            QListWidgetItem(country, self.__country_list)

    def __connect_signals(self):
        self.__search_bar.textChanged.connect(self.__filter_country_list)
        self.__country_list.itemClicked.connect(self.__on_item_clicked)

    def __filter_country_list(self):
        search_text = self.__search_bar.text().lower()
        for i in range(self.__country_list.count()):
            item = self.__country_list.item(i)
            item.setHidden(search_text not in item.text().lower())

    def __on_item_clicked(self, item):
        country_code = self.__countries.from_name(item.text())
        if country_code in self.specific_countries:
            self.specific_countries.remove(country_code)
            item.setBackground(QColor('white'))
        else:
            self.specific_countries.add(country_code)
            item.setBackground(QColor('lightblue'))


class GraphManager:
    def __init__(self, parent_widget):
        self.__image_label = QLabel(parent_widget)
        self.__image_label.setGeometry(100, 200, 1000, 600)
        self.__start_year = None
        self.__end_year = None
        self.__data_processor = DataProcessor()

    def generate_graph(self, specific_countries, years):
        print(f"Generating graph for countries: {specific_countries}, years: {years}")
        
        if self.__set_year_range(years, specific_countries):
            try:
                lines = self.__data_processor.clean_text("resources/car_stat.txt")
                data = self.__data_processor.transform_to_dict(lines)
                graph = GenGraph(data, specific_countries, years[0], years[1])
                graph.save_plot("resources/img.png")
                self.__image_label.setPixmap(QPixmap("resources/img.png").scaled(1000, 600))
            except IndexError as e:
                print(f"Index error during graph generation: {e}")
            except Exception as e:
                print(f"An error occurred during graph generation: {e}")
        else:
            print("Invalid range or no countries selected.")

    def handle_year_button_click(self, year, specific_countries):
        if self.__start_year is None:
            self.__start_year = year
            print(f"Start Year selected: {year}")
        elif self.__end_year is None:
            if year >= self.__start_year:
                self.__end_year = year
                print(f"End Year selected: {year}")
                self.generate_graph(specific_countries, (self.__start_year, self.__end_year))
                self.__reset_year_range()
            else:
                print("End year must be greater than or equal to start year.")
        else:
            self.__start_year = year
            self.__end_year = None
            print(f"Start Year re-selected: {year}")

    def __set_year_range(self, years, specific_countries):
        return (
            bool(years[0]) and
            bool(years[1]) and
            years[0] <= years[1] and
            len(specific_countries) > 0
        )

    def __reset_year_range(self):
        self.__start_year = None
        self.__end_year = None

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__setup_ui()
        self.__setup_logic()

    def __setup_ui(self):
        self.setWindowTitle("My App")
        self.resize(1600, 1100)

        self.__widget = QWidget(self)
        self.setCentralWidget(self.__widget)

        self.__countries = Countries()
        self.__graph_manager = GraphManager(self.__widget)
        self.__country_filter = CountryFilter(self.__widget, self.__countries)
        self.__map_widget = MapWidget(560, 200, 900, 600, self.__widget)

        self.__setup_buttons()
        self.__setup_labels()

    def __setup_buttons(self):
        self.__data_button = BaseButton("Czytaj dane wykresu", 1300, 900, 300, 100, self.fetch_and_display_data, self.__widget)
        self.__convert_map_button = BaseButton("Konwertuj Mapę", 1350, 800, 200, 100, self.convert_map, self.__widget)
        self.__graph_button = BaseButton("Wykres", 40, 40, 760, 80, self.display_graph_view, self.__widget)
        self.__map_button = BaseButton("Mapa", 800, 40, 760, 80, self.display_map_view, self.__widget)
        self.__year_buttons_panel = ButtonsPanel(
            parent=self, 
            callback=lambda year: self.__graph_manager.handle_year_button_click(year, self.__country_filter.specific_countries)
        )
        self.__year_buttons_panel.setGeometry(40, 900, 1100, 50)

    def __setup_labels(self):
        custom_font = QFont("Roboto-MediumItalic", 20)
        custom_font.setBold(True)
        self.__map_label = QLabel(self.__widget)
        self.__map_label.setText("Mapa Stacji Ładowania")
        self.__map_label.setFont(custom_font)
        self.__map_label.setGeometry(100, 200, 400, 50)

    def __setup_logic(self):
        self.__data_fetcher = EurostatDataFetcher()
        self.__voivodeships = Voivodeships()

    def fetch_and_display_data(self):
        response = self.__data_fetcher.get_tsv_data("road_eqr_carpda")
        if response is not None:
            print("Data fetched and saved successfully.")
        else:
            print("Failed to fetch data.")

    def display_map_view(self):
        self.__set_visibility(map_view=True)

    def display_graph_view(self):
        self.__set_visibility(map_view=False)

    def convert_map(self):
        converter = Map()
        converter.txt_to_html()

    def __set_visibility(self, map_view=True):
        self.__map_widget.setVisible(map_view)
        self.__map_label.setVisible(map_view)
        self.__convert_map_button.setVisible(map_view)
        self.__country_filter._CountryFilter__country_list.setVisible(not map_view)
        self.__country_filter._CountryFilter__search_bar.setVisible(not map_view)
        self.__data_button.setVisible(not map_view)
        self.__year_buttons_panel.setVisible(not map_view)
        self.__graph_manager._GraphManager__image_label.setVisible(not map_view)

if __name__ == "__main__":
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
