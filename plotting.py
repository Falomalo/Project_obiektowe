import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


class BasePlot:
    def __init__(self, data, specific_countries, start_year, end_year):
        self._data = data
        self._specific_countries = specific_countries
        self._start_year = start_year
        self._end_year = end_year
        self._years = list(range(start_year, end_year + 1))
        self._num_of_cars = self._get_cars_count()

    def add_new_plot(self):
        fig, ax = plt.subplots(figsize=(15, 8))
        valid_data = self._plot_data(ax)
        if valid_data:
            self._customize_plot(ax)
        return plt

    def _get_cars_count(self):
        num_of_cars = {}
        for year in self._years:
            year_data = self._get_year_data(year)
            num_of_cars[year] = year_data
        return num_of_cars

    def _get_year_data(self, year):
        year_data = []
        for country in self._specific_countries:
            index = year - self._start_year
            if 0 <= index < len(self._data.get(country, [])):
                year_data.append(self._data[country][index])
            else:
                print(f"Year {year} index {index} out of range for country {country}.")
                year_data.append(0)
        return year_data

    def _plot_data(self, ax):
        x = np.arange(len(self._years))
        width = 1 / len(self._specific_countries)
        valid_data = False
        for i, country in enumerate(self._specific_countries):
            offset = width * i
            measurements = self._num_of_cars_for_country(i)
            if any(measurements):
                valid_data = True
            rects = ax.bar(x + offset, measurements, width, label=country)
            ax.bar_label(rects, padding=3)
        return valid_data

    def _num_of_cars_for_country(self, index):
        return [self._num_of_cars[year][index] for year in self._years]

    def _customize_plot(self, ax):
        ax.set_ylabel('Number of Cars')
        ax.set_title(f'Number of Cars by Country and Year ({self._start_year}-{self._end_year})')
        ax.set_xticks(np.arange(len(self._years)))
        ax.set_xticklabels([str(year) for year in self._years])
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1), ncols=1)
        ax.set_ylim(0, self._get_max_y_value() * 1.1)

    def _get_max_y_value(self):
        try:
            max_values = []
            for measurements in self._num_of_cars.values():
                if measurements and any(val > 0 for val in measurements):
                    max_values.append(max(measurements))
            return max(max_values) if max_values else 1
        except:
            return 1

    def save_plot(self, file_path):
        plt_obj = self.add_new_plot()
        plt_obj.savefig(file_path, bbox_inches='tight', dpi=300)
        plt_obj.close()

    def save_plot_to_pdf(self, file_path):
        try:
            plt_obj = self.add_new_plot()

            # Sprawdź czy mamy jakiekolwiek dane do wykreślenia
            valid_data = any(
                any(self._data.get(country, []))
                for country in self._specific_countries
            )

            if not valid_data:
                print("Brak danych do wykreślenia")
                return False

            with PdfPages(file_path) as pdf:
                pdf.savefig(plt_obj.gcf(), bbox_inches='tight', dpi=300)

            plt_obj.close()
            print(f"Wykres zapisany do PDF: {file_path}")
            return True

        except Exception as e:
            print(f"Błąd podczas zapisywania do PDF: {e}")
            import traceback
            traceback.print_exc()
            return False