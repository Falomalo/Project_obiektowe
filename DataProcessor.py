class DataProcessor:
    def __init__(self):
        self.__data_dict = {}

    def transform_to_dict(self, lines):
        self.__data_dict = {}
        
        for line in lines:
            line = line.replace("A,NR,ELC,", "").strip()
            key = line[:2]
            vals = line.split("\t")[1:]
            values = [0 if val.strip() == '' or val.strip() == ':' else int(val.strip().split()[0]) for val in vals]
            values = values[1:]
            self.__data_dict[key] = values

        return self.__data_dict

    def clean_text(self, path):
        lines = []
        with open(path, "r", encoding="utf-8") as f:
            for i in f:
                i = i.strip().split("\\n")
                for j in i:
                    if j != "":
                        lines.append(j[:-3])
        return lines[191 + 14:229 + 14]
