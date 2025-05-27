from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSlider


class Wykres:
    pass


class QtHorizontal:
    pass


class Slider(QWidget):
    #class is for creating a slider to be used in the



    def __init__(self, parent, labels, values_list, colors_list, legend_labels):
        super().__init__(parent)

        self.labels = labels
        self.values_list = values_list
        self.colors_list = colors_list
        self.legend_labels = legend_labels

        self.layout = QVBoxLayout(self)

        self.wykres = Wykres(self, width=8, height=5, dpi=100)
        self.layout.addWidget(self.wykres)

        self.slider_from = self._create_slider()
        self.slider_to = self._create_slider()

        self.layout.addWidget(self.slider_from)
        self.layout.addWidget(self.slider_to)

        self.update_plot()

    def _create_slider(self):
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(len(self.labels) - 1)
        slider.setValue(0)
        slider.valueChanged.connect(self.update_plot)
        return slider

    def update_plot(self):
        from_index = self.slider_from.value()
        to_index = self.slider_to.value()
        if from_index > to_index:
            from_index, to_index = to_index, from_index

        filtered_labels = self.labels[from_index:to_index + 1]
        filtered_values_list = [values[from_index:to_index + 1] for values in self.values_list]

        self.wykres.plot(filtered_labels, filtered_values_list, self.colors_list, self.legend_labels)

    def set_values(self, labels, values_list):
        self.labels = labels
        self.values_list = values_list
        self.slider_from.setMaximum(len(labels) - 1)
        self.slider_to.setMaximum(len(labels) - 1)
        self.update_plot()