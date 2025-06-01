from utils.plotting import BasePlot

class GenGraph(BasePlot):
    def __init__(self, data, specific_countries, start_year, end_year):
        super().__init__(data, specific_countries, start_year, end_year)
