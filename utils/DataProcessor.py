class DataProcessor:
    def __init__(self):
        pass

    def clean_text(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = [line.strip() for line in file if 'GEN,NR' in line]
            print(f"GEN lines found: {len(lines)}")
            return lines
        except Exception as e:
            print(f"Error reading file: {e}")
            return []

    def transform_to_dict(self, lines):
        data = {}

        for line in lines:
            try:
                # Split by space and extract country code
                parts = line.split()
                country_code = parts[0].split(',')[3]  # Get country from A,GEN,NR,DE

                # Parse numeric values
                values = [float(part) for part in parts[1:] if part.replace('.', '').isdigit()]

                # Map to years starting from 2014
                data[country_code] = {str(2014 + i): value for i, value in enumerate(values)}

            except Exception:
                continue

        print(f"Countries in data: {list(data.keys())}")
        return data