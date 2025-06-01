import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap, QColor
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QListWidget, QLineEdit,
                             QListWidgetItem, QLabel, QSlider, QHBoxLayout, QVBoxLayout)
from data.countries import Countries
from data.voivodeships import Voivodeships
from data.eurostat import EurostatDataFetcher
from widgets.base_button import BaseButton
from widgets.map_widget import MapWidget
from widgets.gengraph import GenGraph
from utils import Map
from utils.DataProcessor import DataProcessor


class YearRangeSlider(QWidget):
    """Custom widget with two sliders for selecting year range"""

    def __init__(self, parent, min_year=2010, max_year=2023, callback=None):
        super().__init__(parent)
        self.min_year = min_year
        self.max_year = max_year
        self.callback = callback

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Labels layout
        labels_layout = QHBoxLayout()
        self.start_label = QLabel(f"Start Year: {self.min_year}")
        self.end_label = QLabel(f"End Year: {self.max_year}")
        labels_layout.addWidget(self.start_label)
        labels_layout.addStretch()
        labels_layout.addWidget(self.end_label)

        # Sliders layout
        sliders_layout = QHBoxLayout()

        # Start year slider
        self.start_slider = QSlider(Qt.Horizontal)
        self.start_slider.setMinimum(self.min_year)
        self.start_slider.setMaximum(self.max_year)
        self.start_slider.setValue(self.min_year)
        self.start_slider.valueChanged.connect(self.on_start_year_changed)

        # End year slider
        self.end_slider = QSlider(Qt.Horizontal)
        self.end_slider.setMinimum(self.min_year)
        self.end_slider.setMaximum(self.max_year)
        self.end_slider.setValue(self.max_year)
        self.end_slider.valueChanged.connect(self.on_end_year_changed)

        sliders_layout.addWidget(self.start_slider)
        sliders_layout.addWidget(self.end_slider)

        # Generate button
        self.generate_button = BaseButton("Generate Graph", 0, 0, 200, 40, self.generate_graph, self)

        layout.addLayout(labels_layout)
        layout.addLayout(sliders_layout)
        layout.addWidget(self.generate_button)

    def on_start_year_changed(self, value):
        # Ensure start year doesn't exceed end year
        if value > self.end_slider.value():
            self.end_slider.setValue(value)
        self.start_label.setText(f"Start Year: {value}")

    def on_end_year_changed(self, value):
        # Ensure end year isn't less than start year
        if value < self.start_slider.value():
            self.start_slider.setValue(value)
        self.end_label.setText(f"End Year: {value}")

    def generate_graph(self):
        start_year = self.start_slider.value()
        end_year = self.end_slider.value()
        if self.callback:
            self.callback(start_year, end_year)

    def get_year_range(self):
        return (self.start_slider.value(), self.end_slider.value())


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
        self.__data_processor = DataProcessor()

    def generate_graph(self, specific_countries, years):
        print(f"Generating graph for countries: {specific_countries}, years: {years}")

        if self.__validate_inputs(years, specific_countries):
            try:
                # Step 1: Data processing (this works fine)
                print("Step 1: Processing data...")
                lines = self.__data_processor.clean_text("resources/car_stat.txt")
                data = self.__data_processor.transform_to_dict(lines)

                # Step 2: Debug the data being passed to GenGraph
                print("Step 2: Checking data for requested countries...")
                countries_list = list(specific_countries)  # Convert set to list
                for country in countries_list:
                    if country in data:
                        country_data = {}
                        for year in range(years[0], years[1] + 1):
                            year_str = str(year)
                            if year_str in data[country]:
                                country_data[year_str] = data[country][year_str]

                        if country_data:
                            print(f"✅ {country} data: {country_data}")
                        else:
                            print(f"❌ {country}: No data for years {years[0]}-{years[1]}")
                    else:
                        print(f"❌ {country}: Not found in dataset")

                # Step 3: Try to create GenGraph
                print("Step 3: Creating GenGraph...")
                print(
                    f"Parameters: data={type(data)}, countries={specific_countries}, start={years[0]}, end={years[1]}")

                graph = GenGraph(data, specific_countries, years[0], years[1])
                print("✅ GenGraph created successfully")

                # Step 4: Try to save plot
                print("Step 4: Saving plot...")
                graph.save_plot("resources/img.png")
                print("✅ Plot saved successfully")

                # Step 5: Display image
                print("Step 5: Displaying image...")
                self.__image_label.setPixmap(QPixmap("resources/img.png").scaled(1000, 600))
                print("✅ Image displayed successfully")

            except Exception as e:
                print(f"❌ ERROR at step: {e}")
                print(f"Error type: {type(e)}")
                print(f"Error details: {str(e)}")

                # Check if it's specifically a GenGraph issue
                import traceback
                print("Full traceback:")
                traceback.print_exc()
        else:
            print("Invalid range or no countries selected.")

    def __validate_inputs(self, years, specific_countries):
        return (
                years[0] is not None and
                years[1] is not None and
                years[0] <= years[1] and
                len(specific_countries) > 0
        )


class MapManager:
    """Manager for the new map tab functionality"""

    def __init__(self, parent_widget):
        from widgets.europe_map import EuropeMapWidget  # Import the new widget

        self.__europe_map = EuropeMapWidget(parent_widget)
        self.__europe_map.setGeometry(40, 140, 1520, 700)  # Position and size
        self.__europe_map.load_data()  # Load initial data

        # Setup UI elements for map tab
        self.__setup_ui(parent_widget)

    def __setup_ui(self, parent_widget):
        """Setup UI elements for map tab"""
        # Title label
        font = QFont("Arial", 18)
        self.__title_label = QLabel(parent_widget)
        self.__title_label.setText("Interaktywna Mapa Europy - Dane o Pojazdach")
        self.__title_label.setFont(font)
        self.__title_label.setGeometry(40, 140, 600, 30)
        self.__title_label.setStyleSheet("font-weight: bold; color: #333;")

        # Info label
        self.__info_label = QLabel(parent_widget)
        self.__info_label.setText("Użyj kontrolek powyżej mapy aby zmienić źródło danych, rok lub widok")
        self.__info_label.setGeometry(40, 170, 800, 20)
        self.__info_label.setStyleSheet("color: #666; font-style: italic;")

    def generate_map(self):
        """Generate/refresh the map"""
        print("Refreshing Europe map...")
        self.__europe_map.load_data()
        self.__europe_map.draw_europe_map()

    def get_widgets(self):
        """Return all widgets that belong to this manager"""
        return [self.__europe_map, self.__title_label, self.__info_label]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__current_view = "map"  # Track current view: "map", "graph", "newmap"
        self.__setup_ui()
        self.__setup_logic()

        # Start with map view only
        self.display_map_view()

    def __setup_ui(self):
        self.setWindowTitle("My App")
        self.resize(1600, 1100)

        self.__widget = QWidget(self)
        self.setCentralWidget(self.__widget)

        self.__countries = Countries()
        self.__graph_manager = GraphManager(self.__widget)
        self.__country_filter = CountryFilter(self.__widget, self.__countries)
        self.__map_widget = MapWidget(560, 200, 900, 600, self.__widget)
        self.__map_manager = MapManager(self.__widget)  # New map manager

        self.__setup_buttons()
        self.__setup_labels()
        self.__setup_year_slider()

    def __setup_buttons(self):
        self.__data_button = BaseButton("Czytaj dane wykresu", 1300, 900, 300, 100, self.fetch_and_display_data,
                                        self.__widget)
        self.__convert_map_button = BaseButton("Konwertuj Mapę", 1350, 800, 200, 100, self.convert_map, self.__widget)

        # Updated tab buttons with new layout
        self.__graph_button = BaseButton("Wykres", 40, 40, 506, 80, self.display_graph_view, self.__widget)
        self.__map_button = BaseButton("Mapa", 547, 40, 506, 80, self.display_map_view, self.__widget)
        self.__new_map_button = BaseButton("Nowa Mapa", 1054, 40, 506, 80, self.display_new_map_view, self.__widget)

    def __setup_year_slider(self):
        """Setup the year range slider to replace button panel"""
        self.__year_slider = YearRangeSlider(
            parent=self.__widget,
            min_year=2010,
            max_year=2023,
            callback=self.handle_year_range_selection
        )
        self.__year_slider.setGeometry(40, 850, 1100, 120)

    def handle_year_range_selection(self, start_year, end_year):
        """Handle year range selection from slider"""
        print(f"Year range selected: {start_year} - {end_year}")
        if len(self.__country_filter.specific_countries) > 0:
            self.__graph_manager.generate_graph(
                self.__country_filter.specific_countries,
                (start_year, end_year)
            )
        else:
            print("Please select at least one country first.")

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
        self.__current_view = "map"
        self.__set_visibility(view_type="map")

    def display_graph_view(self):
        self.__current_view = "graph"
        self.__set_visibility(view_type="graph")

    def display_new_map_view(self):
        self.__current_view = "newmap"
        self.__set_visibility(view_type="newmap")

    def convert_map(self):
        converter = Map()
        converter.txt_to_html()

    def __set_visibility(self, view_type="map"):
        # Hide all views first
        self.__map_widget.setVisible(False)
        self.__map_label.setVisible(False)
        self.__convert_map_button.setVisible(False)

        self.__country_filter._CountryFilter__country_list.setVisible(False)
        self.__country_filter._CountryFilter__search_bar.setVisible(False)
        self.__data_button.setVisible(False)
        self.__year_slider.setVisible(False)
        self.__graph_manager._GraphManager__image_label.setVisible(False)

        # Hide all map manager widgets
        for widget in self.__map_manager.get_widgets():
            widget.setVisible(False)

        # Show elements based on current view
        if view_type == "map":
            self.__map_widget.setVisible(True)
            self.__map_label.setVisible(True)
            self.__convert_map_button.setVisible(True)
        elif view_type == "graph":
            self.__country_filter._CountryFilter__country_list.setVisible(True)
            self.__country_filter._CountryFilter__search_bar.setVisible(True)
            self.__data_button.setVisible(True)
            self.__year_slider.setVisible(True)
            self.__graph_manager._GraphManager__image_label.setVisible(True)
        elif view_type == "newmap":
            for widget in self.__map_manager.get_widgets():
                widget.setVisible(True)

        print(f"Switched to {view_type} view")


if __name__ == "__main__":
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())