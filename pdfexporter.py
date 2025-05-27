from utils import DataProcessor
from widgets.gengraph import GenGraph
import os


class PDFExporter:
    def __init__(self, parent_widget):
        self.__parent_widget = parent_widget

    def export_graph_to_pdf(self, graph_manager, specific_countries, years, output_path="wykres.pdf"):
        """Eksportuje aktualny wykres do PDF"""
        if self.__validate_export_params(specific_countries, years):
            try:
                # Upewnij się, że folder istnieje dla wybranej ścieżki
                output_dir = os.path.dirname(output_path)
                if output_dir:  # Jeśli ścieżka zawiera folder
                    os.makedirs(output_dir, exist_ok=True)

                data_processor = DataProcessor()
                lines = data_processor.clean_text("resources/car_stat.txt")

                if not lines:
                    print("Brak danych w pliku car_stat.txt")
                    return False

                data = data_processor.transform_to_dict(lines)

                # Sprawdź czy mamy dane dla wybranych krajów
                available_countries = [c for c in specific_countries if c in data]
                if not available_countries:
                    print("Brak danych dla wybranych krajów")
                    return False

                graph = GenGraph(data, available_countries, years[0], years[1])
                success = graph.save_plot_to_pdf(output_path)

                if success:
                    print(f"Wykres został pomyślnie wyeksportowany do: {output_path}")
                    return True
                else:
                    print("Błąd podczas eksportu do PDF")
                    return False

            except Exception as e:
                print(f"Błąd podczas eksportu wykresu do PDF: {e}")
                return False
        else:
            print("Nieprawidłowe parametry eksportu lub brak wybranych krajów")
            return False

    def __validate_export_params(self, specific_countries, years):
        return (
                len(specific_countries) > 0 and
                years and
                len(years) == 2 and
                years[0] <= years[1]
        )