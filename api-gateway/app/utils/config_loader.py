import json
import os




class ConfigLoader:
    @staticmethod
    def load_config(file_path: str) -> dict:
        """
        Load configuration from a JSON file.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Config file not found: {file_path}")
        with open(file_path, "r") as f:
            return json.load(f)
