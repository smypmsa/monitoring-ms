import aiohttp




class HttpClient:
    """
    Utility for making HTTP requests.
    """

    @staticmethod
    async def get(url):
        """
        Perform an asynchronous HTTP GET request.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    # Return plain text for Prometheus-compatible metrics
                    return await response.text()
                response.raise_for_status()
