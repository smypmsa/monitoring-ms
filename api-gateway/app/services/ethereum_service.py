import asyncio

from app.utils.http_client import HttpClient
from app.utils.config_loader import ConfigLoader
from app.services.base_service import BaseService




CONFIG_PATH = "app/config/endpoints.json"

class EthereumService(BaseService):
    """
    Service to interact with the Ethereum metrics endpoint.
    """

    def __init__(self):
        self.config = ConfigLoader.load_config(CONFIG_PATH)

    async def fetch_metrics(self):
        """
        Fetch metrics from all configured Ethereum endpoints.
        """
        tasks = [
            HttpClient.get(provider["metrics_url"])
            for provider in self.config.get("providers", [])
        ]
        results = await asyncio.gather(*tasks)
        # Concatenate all responses as plain text
        return "\n".join(results)
