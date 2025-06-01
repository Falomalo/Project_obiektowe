import numpy as np
import matplotlib.pyplot as plt


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
        """Get data for all countries for a specific year"""
        year_data = []
        year_str = str(year)  # Convert year to string to match DataProcessor format

        for country in self._specific_countries:
            if country in self._data:
                country_data = self._data[country]
                if year_str in country_data:
                    year_data.append(country_data[year_str])
                else:
                    print(f"Year {year} not found for country {country}.")
                    year_data.append(0)
            else:
                print(f"Country {country} not found in dataset.")
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
        """Get measurements for a specific country across all years"""
        measurements = []
        for year in self._years:
            if year in self._num_of_cars and index < len(self._num_of_cars[year]):
                measurements.append(self._num_of_cars[year][index])
            else:
                measurements.append(0)  # Default to 0 if data missing
        return measurements

    def _customize_plot(self, ax):
        ax.set_ylabel('Number of Cars')
        ax.set_title(f'Number of Cars by Country and Year ({self._start_year}-{self._end_year})')
        ax.set_xticks(np.arange(len(self._years)))
        ax.set_xticklabels([str(year) for year in self._years])
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1), ncols=1)
        ax.set_ylim(0, self._get_max_y_value() * 1.1)

    def _get_max_y_value(self):
        return max(max(measurements) for measurements in self._num_of_cars.values() if measurements)

    def save_plot(self, file_path):
        plt = self.add_new_plot()
        plt.savefig(file_path)