import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap, QColor
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QListWidget, QLineEdit,
                             QListWidgetItem, QLabel, QSlider, QMessageBox, QHBoxLayout, QVBoxLayout, QFileDialog)
from data.countries import Countries
from data.voivodeships import Voivodeships
from data.eurostat import EurostatDataFetcher
from widgets.base_button import BaseButton
from widgets.map_widget import MapWidget
from widgets.gengraph import GenGraph
from utils import Map
from utils import DataProcessor
from pdfexporter import PDFExporter


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
        self.__parent_widget = parent_widget
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
        try:
            search_text = self.__search_bar.text().lower()

            # Prosta walidacja - tylko litery i spacje
            if search_text and not search_text.replace(" ", "").replace("-", "").isalpha():
                self.__show_message("Używaj tylko liter i spacji w wyszukiwaniu")
                return

            for i in range(self.__country_list.count()):
                item = self.__country_list.item(i)
                item.setHidden(search_text not in item.text().lower())
        except:
            print("Błąd filtrowania krajów")

    def __on_item_clicked(self, item):
        try:
            country_code = self.__countries.from_name(item.text())

            if country_code in self.specific_countries:
                self.specific_countries.remove(country_code)
                item.setBackground(QColor('white'))
            else:
                self.specific_countries.add(country_code)
                item.setBackground(QColor('lightblue'))
        except:
            print("Błąd wyboru kraju")

    def __show_message(self, text):
        try:
            msg = QMessageBox()
            msg.setText(text)
            msg.exec_()
        except:
            print(text)


class GraphManager:
    def __init__(self, parent_widget):
        self.__image_label = QLabel(parent_widget)
        self.__image_label.setGeometry(100, 200, 1000, 600)
        self.__start_year = None
        self.__end_year = None
        self.__data_processor = DataProcessor()
        self.__parent_widget = parent_widget
        self.__last_generated_params = None

    def generate_graph(self, specific_countries, years):
        try:
            # Podstawowa walidacja
            if not specific_countries:
                QMessageBox.information(self.__parent_widget, "Brak krajów",
                                        "Proszę wybrać co najmniej jeden kraj z listy.")
                return False

            if not years or years[0] > years[1]:
                self.__show_message("Nieprawidłowy zakres lat")
                return False

            # Przetwarzanie danych
            lines = self.__data_processor.clean_text("resources/car_stat.txt")
            if not lines:
                self.__show_message("Brak danych w pliku")
                return False

            data = self.__data_processor.transform_to_dict(lines)

            # Sprawdź czy wybrane kraje mają dane
            available_countries = [c for c in specific_countries if c in data]
            if not available_countries:
                self.__show_message("Brak danych dla wybranych krajów")
                return False

            # Generuj wykres
            from widgets.gengraph import GenGraph
            graph = GenGraph(data, available_countries, years[0], years[1])
            graph.save_plot("resources/img.png")

            # Wyświetl wykres
            pixmap = QPixmap("resources/img.png")
            if not pixmap.isNull():
                self.__image_label.setPixmap(pixmap.scaled(1000, 600))

                # Zapisz parametry dla eksportu PDF
                self.__last_generated_params = {
                    'countries': specific_countries.copy(),
                    'years': years
                }
                return True
            else:
                self.__show_message("Błąd tworzenia wykresu")
                return False

        except Exception as e:
            print(f"Błąd generowania wykresu: {e}")
            self.__show_message("Błąd podczas tworzenia wykresu")
            return False

    def export_current_graph_to_pdf(self, output_path="resources/wykres.pdf"):
        if self.__last_generated_params:
            pdf_exporter = PDFExporter(None)
            return pdf_exporter.export_graph_to_pdf(
                self,
                self.__last_generated_params['countries'],
                self.__last_generated_params['years'],
                output_path
            )
        else:
            print("Brak wykresu do eksportu. Najpierw wygeneruj wykres.")
            return False

    def handle_year_button_click(self, year, specific_countries):
        try:
            if not specific_countries:
                self.__show_message("Najpierw wybierz kraje")
                return

            if self.__start_year is None:
                self.__start_year = year
                print(f"Rok początkowy: {year}")

            elif self.__end_year is None:
                if year >= self.__start_year:
                    self.__end_year = year
                    print(f"Rok końcowy: {year}")
                    self.generate_graph(specific_countries, (self.__start_year, self.__end_year))
                    self.__reset_year_range()
                else:
                    self.__show_message("Rok końcowy musi być większy lub równy rokowi początkowemu")
            else:
                self.__start_year = year
                self.__end_year = None
                print(f"Nowy rok początkowy: {year}")

        except Exception as e:
            print(f"Błąd obsługi roku: {e}")

    def __reset_year_range(self):
        self.__start_year = None
        self.__end_year = None

    def __show_message(self, text):
        try:
            msg = QMessageBox()
            msg.setText(text)
            msg.exec_()
        except:
            print(text)


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
        self.__setup_year_slider()

    def __setup_buttons(self):
        self.__data_button = BaseButton("Czytaj dane wykresu", 1300, 900, 300, 100, self.fetch_and_display_data,
                                        self.__widget)
        self.__convert_map_button = BaseButton("Konwertuj Mapę", 1350, 800, 200, 100, self.convert_map, self.__widget)
        self.__graph_button = BaseButton("Wykres", 40, 40, 760, 80, self.display_graph_view, self.__widget)
        self.__map_button = BaseButton("Mapa", 800, 40, 760, 80, self.display_map_view, self.__widget)
        self.__export_pdf_button = BaseButton("Eksportuj do PDF", 1200, 750, 200, 50, self.export_graph_to_pdf,
                                              self.__widget)

    def __setup_year_slider(self):
        self.__year_slider = YearRangeSlider(
            parent=self.__widget,
            min_year=2010,
            max_year=2023,
            callback=self.handle_year_range_selection
        )
        self.__year_slider.setGeometry(40, 850, 1100, 120)

    def export_graph_to_pdf(self):
        # Sprawdź czy jest wygenerowany wykres
        if not hasattr(self.__graph_manager, '_GraphManager__last_generated_params') or \
                not self.__graph_manager._GraphManager__last_generated_params:
            QMessageBox.warning(self.__widget, "Błąd",
                                "Najpierw wygeneruj wykres, a następnie możesz go wyeksportować do PDF.")
            return

        # Otwórz dialog wyboru pliku
        file_path, _ = QFileDialog.getSaveFileName(
            self.__widget,
            "Zapisz wykres jako PDF",
            "wykres.pdf",  # nazwa domyślna
            "PDF files (*.pdf);;All files (*.*)"
        )

        if file_path:  # Jeśli użytkownik wybrał plik
            # Upewnij się, że rozszerzenie to .pdf
            if not file_path.lower().endswith('.pdf'):
                file_path += '.pdf'

            success = self.__graph_manager.export_current_graph_to_pdf(file_path)
            if success:
                QMessageBox.information(self.__widget, "Sukces",
                                        f"Wykres został pomyślnie wyeksportowany do:\n{file_path}")
            else:
                QMessageBox.warning(self.__widget, "Błąd",
                                    "Nie udało się wyeksportować wykresu do PDF.")
        # Jeśli użytkownik anulował dialog, nic nie robimy

    def handle_year_range_selection(self, start_year, end_year):
        print(f"Year range selected: {start_year} - {end_year}")
        if len(self.__country_filter.specific_countries) > 0:
            self.__graph_manager.generate_graph(
                self.__country_filter.specific_countries,
                (start_year, end_year)
            )
        else:
            QMessageBox.information(self.__widget, "No Country Selected", "Please select at least one country.")

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
        try:
            response = self.__data_fetcher.get_tsv_data("road_eqr_carpda")
            if response:
                self.__show_message("Dane pobrane pomyślnie")
            else:
                self.__show_message("Nie udało się pobrać danych")
        except Exception as e:
            print(f"Błąd pobierania danych: {e}")
            self.__show_message("Błąd podczas pobierania danych")

    def display_map_view(self):
        self.__set_visibility(map_view=True)

    def display_graph_view(self):
        self.__set_visibility(map_view=False)

    def convert_map(self):
        try:
            from utils import Map
            converter = Map()
            converter.txt_to_html()
            self.__show_message("Mapa wygenerowana pomyślnie")
        except FileNotFoundError:
            self.__show_message("Nie znaleziono pliku z danymi stacji")
        except Exception as e:
            print(f"Błąd konwersji mapy: {e}")
            self.__show_message("Błąd podczas tworzenia mapy")

    def __set_visibility(self, map_view=True):
        # Map view elements
        self.__map_widget.setVisible(map_view)
        self.__map_label.setVisible(map_view)
        self.__convert_map_button.setVisible(map_view)

        # Graph view elements
        self.__country_filter._CountryFilter__country_list.setVisible(not map_view)
        self.__country_filter._CountryFilter__search_bar.setVisible(not map_view)
        self.__data_button.setVisible(not map_view)
        self.__year_slider.setVisible(not map_view)
        self.__graph_manager._GraphManager__image_label.setVisible(not map_view)

        # PDF export button - only visible in graph view
        self.__export_pdf_button.setVisible(not map_view)

    def __show_message(self, text):
        try:
            msg = QMessageBox()
            msg.setText(text)
            msg.exec_()
        except:
            print(text)


if __name__ == "__main__":
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())