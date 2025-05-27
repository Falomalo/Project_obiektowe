class DataProcessor:
    def __init__(self):
        self.__data_dict = {}

    def transform_to_dict(self, lines):
        self.__data_dict = {}

        for line in lines:
            try:
                line = line.replace("A,NR,ELC,", "").strip()
                key = line[:2]
                vals = line.split("\t")[1:]
                values = []

                for val in vals:
                    try:
                        if val.strip() == '' or val.strip() == ':':
                            values.append(0)  # Domyślna wartość
                        else:
                            values.append(int(val.strip().split()[0]))
                    except:
                        values.append(0)  # Bezpieczna wartość domyślna

                if len(values) > 1:
                    values = values[1:]
                self.__data_dict[key] = values

            except:
                print(f"Błąd przetwarzania linii: {line}")
                continue

        return self.__data_dict

    def clean_text(self, path):
        try:
            lines = []
            with open(path, "r", encoding="utf-8") as f:
                for i in f:
                    i = i.strip().split("\\n")
                    for j in i:
                        if j != "":
                            lines.append(j[:-3])
            return lines[191 + 14:229 + 14]
        except FileNotFoundError:
            print(f"Nie znaleziono pliku: {path}")
            return []
        except:
            print(f"Błąd odczytu pliku: {path}")
            return []