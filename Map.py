import folium
import pandas as pd
import os

class Map:
    def load_map(self):
        self.__load_station_data()

    def txt_to_html(self):
        __geo_final_data = self.__read_txt_data()
        latitudes, longitudes, labels = self.__extract_coordinates_and_labels(__geo_final_data)

        _PROPERTIES = "Properties"
        _LATITUDE = "Latitude"
        _LONGITUDE = "Longitude"

        df = pd.DataFrame({_PROPERTIES: labels,
                           _LATITUDE: latitudes,
                           _LONGITUDE: longitudes})

        m = folium.Map(location=[52, 20], tiles="OpenStreetMap", zoom_start=7)

        for i in range(len(df)):
            folium.Marker(
                location=[df.iloc[i][_LATITUDE], df.iloc[i][_LONGITUDE]],
                popup=df.iloc[i][_PROPERTIES],
            ).add_to(m)
        
        click_js = """
                function addMarker(e) {
                    var coords = e.latlng;
                    var marker = L.marker([coords.lat, coords.lng]).addTo(map);
                    pyjs.handleClick(coords.lat, coords.lng);
                }
                map.on('click', addMarker);
                """
        folium.Map.add_child(m, folium.Element(f'<script>{click_js}</script>'))
        m.save("resources/map.html", close_file=False)
        print("Map file generated and saved at: resources/map.html")

    def __load_station_data(self):
        with open("resources/stacje.txt", "r", encoding="utf-8") as f:
            for line in f:
                print(line.strip())

    def __read_txt_data(self):
        geo_final_data = []
        with open("resources/stacje.txt", "r", encoding="utf-8") as f:
            for line in f:
                geo_final_data.append(line.split())
        return geo_final_data

    def __extract_coordinates_and_labels(self, geo_final_data):
        latitudes = []
        longitudes = []
        labels = []

        for latitude, longitude, *label in geo_final_data:
            latitudes.append(latitude)
            longitudes.append(longitude)
            labels.append(" ".join(label))

        return latitudes, longitudes, labels
