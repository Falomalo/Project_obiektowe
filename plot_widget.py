from utils.plotting import BasePlot
import numpy as np
import matplotlib.pyplot as plt

class PlotWidget(BasePlot):
    def add_new_plot(self):
        x = np.arange(len(self.num_of_cars))
        width = 1 / len(self.specific_countries)
        fig, ax = plt.subplots(figsize=(15, 8))

        for i, country in enumerate(self.specific_countries):
            offset = width * i
            try:
                measurements = [self.num_of_cars[year][i] for year in self.years]
            except IndexError:
                print(f"IndexError: No data for country {country} at index {i}. Using default value 0.")
                measurements = [0] * len(self.years)
            
            rects = ax.bar(x + offset, measurements, width, label=country)
            ax.bar_label(rects, padding=3)

        ax.set_ylabel('Number of Cars')
        ax.set_title('Number of Cars by Country and Year')
        ax.set_xticks(x)
        ax.set_xticklabels(self.years)
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1), ncols=1)
        ax.set_ylim(0, max(max(measurements) for measurements in self.num_of_cars.values() if measurements) * 1.1)

        return plt
