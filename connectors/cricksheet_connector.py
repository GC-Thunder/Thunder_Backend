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

    def extract_latest_file(self, zip_bytes):
        match_data = None
        file_path = None

        with zipfile.ZipFile(zip_bytes) as z:
            last_file = z.namelist()[-1]
            file_path = os.path.join(self.save_dir, last_file)

            with z.open(last_file) as f:
                match_data = json.load(f)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(match_data, f, indent=4, ensure_ascii=False)

        # Cleanup saved file if needed
        if self.cleanup and file_path and os.path.exists(file_path):
            os.remove(file_path)

        return match_data

    def run(self):
        with self.download_zip() as zip_bytes:
            return self.extract_latest_file(zip_bytes)


"""
example of how the function is called 

# To keep the saved file
downloader = IPLJsonDownloader()
data = downloader.run()

# Or, to delete the saved JSON file after reading:
temp_downloader = IPLJsonDownloader(cleanup=True)
temp_data = temp_downloader.run()

"""