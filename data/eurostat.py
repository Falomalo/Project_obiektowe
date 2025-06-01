import requests

class EurostatAPI:
    def get_json_eurostat(self, indicator_code):
        try:
            response = requests.get(f"https://api.eurostat.eu/data/{indicator_code}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return None

eurostat = EurostatAPI()

class EurostatDataFetcher:
    def __init__(self, output_file="resources/car_stat.txt"):
        self.__output_file = output_file
        self.__eurostat = EurostatAPI()
    def get_tsv_data(self, data_name):
        try:
            url = f"https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/{data_name}/?format=TSV"
            response = requests.get(url)
            response.raise_for_status()

            with open(self.__output_file, "w", encoding='utf-8') as f:
                f.write(response.text)

            return response

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return None
        except OSError as e:
            print(f"Error writing file: {e}")
            return None
