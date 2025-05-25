class Countries:
    def __init__(self):
        self.__country_mapping = {
            "Austria": "AT",
            "Belgia": "BE",
            "Bułgaria": "BG",
            "Chorwacja": "HR",
            "Cypr": "CY",
            "Czechy": "CZ",
            "Dania": "DK",
            "Estonia": "EE",
            "Finlandia": "FI",
            "Francja": "FR",
            "Grecja": "EL",
            "Hiszpania": "ES",
            "Holandia": "NL",
            "Irlandia": "IE",
            "Islandia": "IS",
            "Litwa": "LT",
            "Luksemburg": "LU",
            "Łotwa": "LV",
            "Malta": "MT",
            "Niemcy": "DE",
            "Norwegia": "NO",
            "Polska": "PL",
            "Portugalia": "PT",
            "Rumunia": "RO",
            "Szwajcaria": "CH",
            "Szwecja": "SE",
            "Słowacja": "SK",
            "Słowenia": "SI",
            "Węgry": "HU",
            "Włochy": "IT"
        }

    def as_array(self):
        return list(self.__country_mapping.keys())

    def from_name(self, name):
        return self.__country_mapping.get(name, "Unknown country")
