from abc import ABC, abstractmethod

class BaseService(ABC):
    """
    Abstract base class for all services.
    Defines the contract for fetching metrics.
    """

    @abstractmethod
    async def fetch_metrics(self):
        """
        Abstract method to fetch metrics.
        Must be implemented by all subclasses.
        """
        pass