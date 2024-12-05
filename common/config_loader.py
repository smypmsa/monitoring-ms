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
            config = json.load(f)

        for provider in config.get("providers", []):
            if not provider.get("websocket_endpoint"):
                raise KeyError(f"Provider {provider.get('name')} is missing 'websocket_endpoint'")
            
            if not provider.get("http_endpoint"):
                raise KeyError(f"Provider {provider.get('name')} is missing 'http_endpoint'")

        return config

    @staticmethod
    def load_secrets(file_path: str) -> dict:
        """
        Load secrets from a JSON file.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Secrets file not found: {file_path}")
        
        with open(file_path, "r") as f:
            return json.load(f)