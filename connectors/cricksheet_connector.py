import os
import zipfile
import requests
import json
from io import BytesIO

class CricksheetCrickinfo:
    def __init__(self, url="https://cricsheet.org/downloads/ipl_json.zip", save_dir="ipl/BTB", cleanup=False):
        self.url = url
        self.save_dir = save_dir
        self.cleanup = cleanup
        os.makedirs(self.save_dir, exist_ok=True)

    def download_zip(self):
        response = requests.get(self.url)
        response.raise_for_status()
        return BytesIO(response.content)

    def extract_latest_files(self, zip_bytes, n):
        match_data_list = []

        with zipfile.ZipFile(zip_bytes) as z:
            file_names = sorted([name for name in z.namelist() if name.endswith(".json")])[-n:]

            for file_name in file_names:
                file_path = os.path.join(self.save_dir, file_name)
                
                with z.open(file_name) as f:
                    match_data = json.load(f)
                
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(match_data, f, indent=4, ensure_ascii=False)

                match_data_list.append(match_data)

                if self.cleanup and os.path.exists(file_path):
                    os.remove(file_path)

        return match_data_list

    def run(self, n=1):
        with self.download_zip() as zip_bytes:
            return self.extract_latest_files(zip_bytes, n)
