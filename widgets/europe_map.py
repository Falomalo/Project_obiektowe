import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Polygon
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import json
import os
import urllib.request
import zipfile
import shutil

# Import optional dependencies
try:
    import geopandas as gpd

    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False
    print("GeoPandas not installed. Install with: pip install geopandas")

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Requests not installed. Install with: pip install requests")


class EuropeMapWidget(QWidget):
    """Interactive Europe Map Widget with real country borders"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.current_data_source = "env_waselvt"
        self.vehicle_data = {}
        self.country_shapes = {}
        self.setup_ui()
        self.load_country_borders()
        self.setup_map()

    def setup_ui(self):
        """Setup the UI layout"""
        layout = QVBoxLayout(self)

        # Control panel
        control_layout = QHBoxLayout()

        # Data source selector
        self.data_source_label = QLabel("Źródło danych:")
        self.data_source_combo = QComboBox()
        self.data_source_combo.addItems([
            "env_waselvt - Pojazdy utylizowane",
            "tran_r_elvehst - Pojazdy elektryczne"
        ])
        self.data_source_combo.currentTextChanged.connect(self.on_data_source_changed)

        # Map view selector
        self.map_view_label = QLabel("Widok mapy:")
        self.map_view_combo = QComboBox()
        self.map_view_combo.addItems(["Europa", "Polska"])
        self.map_view_combo.currentTextChanged.connect(self.on_map_view_changed)

        # Year selector
        self.year_label = QLabel("Rok:")
        self.year_combo = QComboBox()
        self.year_combo.addItems([str(year) for year in range(2014, 2024)])
        self.year_combo.setCurrentText("2023")
        self.year_combo.currentTextChanged.connect(self.on_year_changed)

        # Download button
        self.download_btn = QPushButton("Pobierz dane geograficzne")
        self.download_btn.clicked.connect(self.download_geographic_data)

        control_layout.addWidget(self.data_source_label)
        control_layout.addWidget(self.data_source_combo)
        control_layout.addWidget(self.map_view_label)
        control_layout.addWidget(self.map_view_combo)
        control_layout.addWidget(self.year_label)
        control_layout.addWidget(self.year_combo)
        control_layout.addWidget(self.download_btn)
        control_layout.addStretch()

        # Info panel
        self.info_label = QLabel("Najedź kursorem na kraj aby zobaczyć szczegóły")
        self.info_label.setStyleSheet("padding: 10px; border: 1px solid #ccc; background-color: #f9f9f9;")

        layout.addLayout(control_layout)
        layout.addWidget(self.info_label)

        # Map canvas
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.canvas.mpl_connect('button_press_event', self.on_mouse_click)

        layout.addWidget(self.canvas)

    def load_country_borders(self):
        """Load country borders from various sources"""
        # Try different methods to load borders
        if self.load_from_geopandas():
            print("Loaded borders from GeoPandas")
            return
        elif self.load_from_local_geojson():
            print("Loaded borders from local GeoJSON")
            return
        elif self.load_from_eurostat_geojson():
            print("Loaded borders from Eurostat")
            return
        else:
            print("Using simplified borders (rectangles)")
            self.load_simplified_borders()

    def load_from_geopandas(self):
        """Try to load borders using GeoPandas"""
        if not GEOPANDAS_AVAILABLE:
            return False

        try:
            # Try to use Natural Earth data
            world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

            # Filter for European countries
            europe = world[world['continent'] == 'Europe']

            # Also include countries partially in Europe
            additional_countries = ['Turkey', 'Russia', 'Kazakhstan', 'Georgia', 'Armenia', 'Azerbaijan', 'Cyprus']
            additional = world[world['name'].isin(additional_countries)]

            self.gdf = gpd.GeoDataFrame(pd.concat([europe, additional], ignore_index=True))

            # Store country shapes
            for idx, row in self.gdf.iterrows():
                if row['iso_a2'] != '-99':  # Valid country code
                    self.country_shapes[row['iso_a2']] = {
                        'geometry': row['geometry'],
                        'name': row['name'],
                        'coords': self.extract_coords(row['geometry'])
                    }

            return True
        except Exception as e:
            print(f"Failed to load from GeoPandas: {e}")
            return False

    def load_from_local_geojson(self):
        """Try to load from local GeoJSON files"""
        geojson_files = [
            'europe_countries.geojson',
            'data/europe_countries.geojson',
            'resources/europe_countries.geojson',
            '../data/europe_countries.geojson'
        ]

        for filepath in geojson_files:
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        return self.process_geojson(data)
                except Exception as e:
                    print(f"Failed to load {filepath}: {e}")

        return False

    def load_from_eurostat_geojson(self):
        """Try to load GeoJSON from Eurostat"""
        if not REQUESTS_AVAILABLE:
            return False

        try:
            # Eurostat provides country boundaries in various formats
            url = "https://gisco-services.ec.europa.eu/distribution/v2/countries/geojson/CNTR_RG_01M_2020_4326.geojson"

            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return self.process_geojson(data)
        except Exception as e:
            print(f"Failed to load from Eurostat: {e}")

        return False

    def process_geojson(self, data):
        """Process GeoJSON data into country shapes"""
        try:
            for feature in data['features']:
                properties = feature.get('properties', {})
                geometry = feature.get('geometry', {})

                # Try different property names for country code
                country_code = (properties.get('ISO_A2') or
                                properties.get('iso_a2') or
                                properties.get('CNTR_ID') or
                                properties.get('id', ''))[:2]

                # Try different property names for country name
                country_name = (properties.get('NAME') or
                                properties.get('name') or
                                properties.get('CNTR_NAME') or
                                properties.get('NAME_ENGL') or
                                'Unknown')

                if country_code and geometry:
                    coords = self.extract_coords_from_geojson(geometry)
                    if coords:
                        self.country_shapes[country_code] = {
                            'geometry': geometry,
                            'name': country_name,
                            'coords': coords
                        }

            return len(self.country_shapes) > 0
        except Exception as e:
            print(f"Failed to process GeoJSON: {e}")
            return False

    def extract_coords_from_geojson(self, geometry):
        """Extract coordinates from GeoJSON geometry"""
        coords = []

        if geometry['type'] == 'Polygon':
            coords = geometry['coordinates'][0]  # Outer ring
        elif geometry['type'] == 'MultiPolygon':
            # Take the largest polygon
            largest = max(geometry['coordinates'], key=lambda x: len(x[0]))
            coords = largest[0]

        return coords

    def extract_coords(self, geometry):
        """Extract coordinates from shapely geometry"""
        if hasattr(geometry, 'exterior'):
            return list(geometry.exterior.coords)
        elif hasattr(geometry, 'geoms'):
            # MultiPolygon - take the largest
            largest = max(geometry.geoms, key=lambda x: x.area)
            return list(largest.exterior.coords)
        return []

    def load_simplified_borders(self):
        """Load simplified rectangular borders as fallback"""
        self.country_shapes = {
            'PL': {
                'coords': [(14.12, 54.84), (24.15, 54.84), (24.15, 49.00), (14.12, 49.00)],
                'name': 'Poland'
            },
            'DE': {
                'coords': [(5.99, 54.98), (15.02, 54.98), (15.02, 47.27), (5.99, 47.27)],
                'name': 'Germany'
            },
            'FR': {
                'coords': [(-4.79, 51.09), (9.56, 51.09), (9.56, 41.33), (-4.79, 41.33)],
                'name': 'France'
            },
            'ES': {
                'coords': [(-9.29, 43.79), (3.34, 43.79), (3.34, 36.00), (-9.29, 36.00)],
                'name': 'Spain'
            },
            'IT': {
                'coords': [(6.63, 47.09), (18.52, 47.09), (18.52, 36.65), (6.63, 36.65)],
                'name': 'Italy'
            },
            'UK': {
                'coords': [(-8.17, 58.64), (1.75, 58.64), (1.75, 49.96), (-8.17, 49.96)],
                'name': 'United Kingdom'
            },
            'NO': {
                'coords': [(4.65, 71.18), (31.10, 71.18), (31.10, 57.98), (4.65, 57.98)],
                'name': 'Norway'
            },
            'SE': {
                'coords': [(11.03, 69.06), (24.16, 69.06), (24.16, 55.34), (11.03, 55.34)],
                'name': 'Sweden'
            },
            'FI': {
                'coords': [(20.65, 70.09), (31.59, 70.09), (31.59, 59.81), (20.65, 59.81)],
                'name': 'Finland'
            },
            'AT': {
                'coords': [(9.53, 49.02), (17.16, 49.02), (17.16, 46.37), (9.53, 46.37)],
                'name': 'Austria'
            },
            'CZ': {
                'coords': [(12.24, 51.06), (18.87, 51.06), (18.87, 48.55), (12.24, 48.55)],
                'name': 'Czech Republic'
            },
            'SK': {
                'coords': [(16.85, 49.61), (22.54, 49.61), (22.54, 47.73), (16.85, 47.73)],
                'name': 'Slovakia'
            },
            'HU': {
                'coords': [(16.11, 48.62), (22.71, 48.62), (22.71, 45.74), (16.11, 45.74)],
                'name': 'Hungary'
            },
            'RO': {
                'coords': [(20.22, 48.22), (29.66, 48.22), (29.66, 43.61), (20.22, 43.61)],
                'name': 'Romania'
            },
            'BG': {
                'coords': [(22.36, 44.22), (28.61, 44.22), (28.61, 41.24), (22.36, 41.24)],
                'name': 'Bulgaria'
            },
            'GR': {
                'coords': [(19.38, 41.75), (28.25, 41.75), (28.25, 34.93), (19.38, 34.93)],
                'name': 'Greece'
            },
            'HR': {
                'coords': [(13.50, 46.54), (19.39, 46.54), (19.39, 42.48), (13.50, 42.48)],
                'name': 'Croatia'
            },
            'SI': {
                'coords': [(13.38, 46.86), (16.57, 46.86), (16.57, 45.42), (13.38, 45.42)],
                'name': 'Slovenia'
            },
            'BE': {
                'coords': [(2.51, 51.48), (6.40, 51.48), (6.40, 49.50), (2.51, 49.50)],
                'name': 'Belgium'
            },
            'NL': {
                'coords': [(3.31, 53.51), (7.21, 53.51), (7.21, 50.80), (3.31, 50.80)],
                'name': 'Netherlands'
            },
            'LU': {
                'coords': [(5.73, 50.18), (6.53, 50.18), (6.53, 49.44), (5.73, 49.44)],
                'name': 'Luxembourg'
            },
            'DK': {
                'coords': [(8.09, 57.75), (12.69, 57.75), (12.69, 54.56), (8.09, 54.56)],
                'name': 'Denmark'
            },
            'IE': {
                'coords': [(-10.48, 55.43), (-5.99, 55.43), (-5.99, 51.43), (-10.48, 51.43)],
                'name': 'Ireland'
            },
            'PT': {
                'coords': [(-9.50, 42.15), (-6.19, 42.15), (-6.19, 36.98), (-9.50, 36.98)],
                'name': 'Portugal'
            },
            'EE': {
                'coords': [(21.76, 59.66), (28.21, 59.66), (28.21, 57.52), (21.76, 57.52)],
                'name': 'Estonia'
            },
            'LV': {
                'coords': [(20.95, 58.08), (28.18, 58.08), (28.18, 55.68), (20.95, 55.68)],
                'name': 'Latvia'
            },
            'LT': {
                'coords': [(20.94, 56.37), (26.82, 56.37), (26.82, 53.91), (20.94, 53.91)],
                'name': 'Lithuania'
            }
        }

    def setup_map(self):
        """Setup the initial map"""
        self.ax = self.figure.add_subplot(111)
        self.load_data()
        self.draw_europe_map()

    def draw_europe_map(self):
        """Draw the Europe map with country boundaries"""
        self.ax.clear()
        self.ax.set_title("Mapa Europy - Dane o pojazdach", fontsize=16, fontweight='bold')

        # Draw countries
        for country_code, country_data in self.country_shapes.items():
            coords = country_data['coords']
            if coords:
                # Create polygon
                polygon = Polygon(coords,
                                  facecolor=self.get_country_color(country_code),
                                  edgecolor='black',
                                  linewidth=0.5,
                                  alpha=0.8)
                self.ax.add_patch(polygon)

                # Add country label
                if len(coords) > 2:
                    # Calculate centroid
                    x_coords = [c[0] for c in coords]
                    y_coords = [c[1] for c in coords]
                    centroid_x = sum(x_coords) / len(x_coords)
                    centroid_y = sum(y_coords) / len(y_coords)

                    # Only show labels for countries with data or major countries
                    if country_code in self.vehicle_data or country_code in ['DE', 'FR', 'IT', 'ES', 'PL', 'UK']:
                        self.ax.text(centroid_x, centroid_y, country_code,
                                     ha='center', va='center', fontsize=8, fontweight='bold')

        # Set map limits
        self.ax.set_xlim(-12, 32)
        self.ax.set_ylim(35, 72)
        self.ax.set_aspect('equal')
        self.ax.axis('off')

        # Add colorbar legend
        self.add_colorbar()

        self.canvas.draw()

    def get_country_color(self, country_code):
        """Get color for country based on data value"""
        if country_code not in self.vehicle_data:
            return '#f0f0f0'  # Gray for no data

        value = self.vehicle_data[country_code]

        # Normalize value to color scale (0-1)
        if self.vehicle_data:
            max_val = max(self.vehicle_data.values())
            min_val = min(self.vehicle_data.values())
            if max_val > min_val:
                normalized = (value - min_val) / (max_val - min_val)
            else:
                normalized = 0.5
        else:
            normalized = 0.5

        # Color scale from light yellow to dark red
        colors = plt.cm.YlOrRd(normalized)
        return colors

    def add_colorbar(self):
        """Add colorbar legend to the map"""
        if not self.vehicle_data:
            return

        # Create colorbar
        sm = plt.cm.ScalarMappable(
            cmap=plt.cm.YlOrRd,
            norm=plt.Normalize(
                vmin=min(self.vehicle_data.values()) if self.vehicle_data else 0,
                vmax=max(self.vehicle_data.values()) if self.vehicle_data else 1
            )
        )
        sm.set_array([])

        cbar = self.figure.colorbar(sm, ax=self.ax, shrink=0.8, aspect=20)

        if self.current_data_source == "env_waselvt":
            cbar.set_label('Liczba pojazdów utylizowanych', rotation=270, labelpad=20)
        else:
            cbar.set_label('Pojazdy elektryczne (%)', rotation=270, labelpad=20)

    def on_mouse_move(self, event):
        """Handle mouse movement over the map"""
        if event.inaxes != self.ax or event.xdata is None or event.ydata is None:
            return

        # Check which country is under cursor
        country = self.get_country_at_point(event.xdata, event.ydata)

        if country:
            country_name = self.country_shapes[country]['name']
            value = self.vehicle_data.get(country, "Brak danych")

            info_text = f"Kraj: {country_name} ({country})\n"
            info_text += f"Rok: {self.year_combo.currentText()}\n"

            if isinstance(value, (int, float)):
                if self.current_data_source == "env_waselvt":
                    info_text += f"Pojazdy utylizowane: {value:,.0f}"
                else:
                    info_text += f"Pojazdy elektryczne: {value:.1f}%"
            else:
                info_text += f"Dane: {value}"

            self.info_label.setText(info_text)
        else:
            self.info_label.setText("Najedź kursorem na kraj aby zobaczyć szczegóły")

    def get_country_at_point(self, x, y):
        """Determine which country contains the given point"""
        for country_code, country_data in self.country_shapes.items():
            if self.point_in_polygon(x, y, country_data['coords']):
                return country_code
        return None

    def point_in_polygon(self, x, y, polygon):
        """Check if point is inside polygon using ray casting algorithm"""
        if not polygon or len(polygon) < 3:
            return False

        n = len(polygon)
        inside = False

        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def on_mouse_click(self, event):
        """Handle mouse clicks on the map"""
        if event.inaxes != self.ax or event.xdata is None or event.ydata is None:
            return

        country = self.get_country_at_point(event.xdata, event.ydata)
        if country:
            print(f"Clicked on {country} - {self.country_shapes[country]['name']}")

    def on_data_source_changed(self, source_text):
        """Handle data source change"""
        if "env_waselvt" in source_text:
            self.current_data_source = "env_waselvt"
        else:
            self.current_data_source = "tran_r_elvehst"

        self.load_data()
        self.draw_europe_map()

    def on_map_view_changed(self, view):
        """Handle map view change"""
        if view == "Europa":
            self.draw_europe_map()
        else:
            self.draw_poland_map()

    def on_year_changed(self, year):
        """Handle year change"""
        self.load_data()
        self.draw_europe_map()

    def draw_poland_map(self):
        """Draw detailed map of Poland"""
        self.ax.clear()
        self.ax.set_title("Mapa Polski - Dane o pojazdach", fontsize=16, fontweight='bold')

        # Simplified Poland regions
        poland_regions = {
            'mazowieckie': {
                'coords': [(20.0, 53.0), (22.5, 53.0), (22.5, 51.0), (20.0, 51.0)],
                'name': 'Mazowieckie'
            },
            'śląskie': {
                'coords': [(18.0, 50.5), (19.5, 50.5), (19.5, 49.0), (18.0, 49.0)],
                'name': 'Śląskie'
            },
            'wielkopolskie': {
                'coords': [(15.5, 53.0), (18.0, 53.0), (18.0, 51.0), (15.5, 51.0)],
                'name': 'Wielkopolskie'
            },
            'małopolskie': {
                'coords': [(19.0, 50.5), (21.0, 50.5), (21.0, 49.0), (19.0, 49.0)],
                'name': 'Małopolskie'
            },
            'dolnośląskie': {
                'coords': [(15.0, 51.5), (17.5, 51.5), (17.5, 50.0), (15.0, 50.0)],
                'name': 'Dolnośląskie'
            },
            'pomorskie': {
                'coords': [(17.0, 54.5), (19.5, 54.5), (19.5, 53.0), (17.0, 53.0)],
                'name': 'Pomorskie'
            }
        }

        for region_code, region_data in poland_regions.items():
            polygon = Polygon(region_data['coords'],
                              facecolor='lightblue',
                              edgecolor='black',
                              linewidth=0.8,
                              alpha=0.7)
            self.ax.add_patch(polygon)

            # Calculate centroid
            x_coords = [c[0] for c in region_data['coords']]
            y_coords = [c[1] for c in region_data['coords']]
            centroid_x = sum(x_coords) / len(x_coords)
            centroid_y = sum(y_coords) / len(y_coords)

            self.ax.text(centroid_x, centroid_y, region_data['name'],
                         ha='center', va='center', fontsize=10, fontweight='bold')

        self.ax.set_xlim(14, 24)
        self.ax.set_ylim(49, 55)
        self.ax.set_aspect('equal')
        self.ax.axis('off')

        self.canvas.draw()

    def load_data(self):
        """Load data for selected source and year"""
        year = int(self.year_combo.currentText())

        # All European country codes
        all_countries = ['AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR',
                         'DE', 'GR', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL',
                         'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE', 'UK', 'NO', 'CH']

        if self.current_data_source == "env_waselvt":
            # Sample data for waste/recycled vehicles
            self.vehicle_data = {}
            base_values = {
                'DE': 500000, 'FR': 400000, 'UK': 380000, 'IT': 350000, 'ES': 300000,
                'PL': 250000, 'NL': 200000, 'BE': 180000, 'SE': 170000, 'AT': 160000,
                'CZ': 140000, 'PT': 130000, 'GR': 120000, 'HU': 110000, 'RO': 100000,
                'DK': 90000, 'FI': 85000, 'SK': 80000, 'NO': 75000, 'IE': 70000,
                'BG': 65000, 'HR': 60000, 'LT': 55000, 'SI': 50000, 'LV': 45000,
                'EE': 40000, 'CY': 35000, 'LU': 30000, 'MT': 25000, 'CH': 150000
            }

            for country, base_value in base_values.items():
                growth_factor = 1 + (year - 2014) * 0.03
                self.vehicle_data[country] = int(base_value * growth_factor)

        else:
            # Sample data for electric vehicles (percentage)
            self.vehicle_data = {}
            base_rates = {
                'NO': 15.0, 'NL': 12.0, 'SE': 10.0, 'DK': 9.0, 'DE': 8.0,
                'UK': 7.5, 'FR': 7.0, 'BE': 6.5, 'AT': 6.0, 'CH': 5.5,
                'FI': 5.0, 'LU': 4.5, 'PT': 4.0, 'ES': 3.5, 'IT': 3.0,
                'IE': 2.8, 'SI': 2.5, 'CZ': 2.2, 'HU': 2.0, 'PL': 1.8,
                'EE': 1.6, 'LT': 1.5, 'SK': 1.4, 'LV': 1.3, 'GR': 1.2,
                'HR': 1.1, 'RO': 1.0, 'BG': 0.9, 'CY': 0.8, 'MT': 0.7
            }

            for country, base_rate in base_rates.items():
                yearly_growth = (year - 2014) * 0.5
                self.vehicle_data[country] = base_rate + yearly_growth

    def download_geographic_data(self):
        """Download geographic data from online sources"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Pobieranie danych geograficznych")
        msg.setText("Możesz pobrać dane granic państw z następujących źródeł:\n\n"
                    "1. Natural Earth (zalecane):\n"
                    "   https://www.naturalearthdata.com/\n"
                    "   Pobierz: Admin 0 - Countries (10m)\n\n"
                    "2. Eurostat GISCO:\n"
                    "   https://ec.europa.eu/eurostat/web/gisco/geodata/reference-data/administrative-units-statistical-units\n"
                    "   Pobierz: Countries 2020\n\n"
                    "3. OpenStreetMap:\n"
                    "   https://download.geofabrik.de/europe.html\n\n"
                    "Po pobraniu umieść pliki .shp, .geojson lub .json w folderze z aplikacją.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def update_data(self, new_data):
        """Update map with new data"""
        self.vehicle_data = new_data
        self.draw_europe_map()


# Example usage
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = EuropeMapWidget()
    widget.show()
    sys.exit(app.exec_())

