import asyncio
from app.metrics.http_call_latency import HttpCallLatencyMetric

async def test_http_call_latency():
    """
    Test the HttpCallLatencyMetric for a single provider.
    """
    metric = HttpCallLatencyMetric(
        blockchain_name="Ethereum",
        endpoint="...",
        provider="Chainstack (Geth)",
        timeout=15,
        interval=30
    )

    result = await metric.collect_metric()
    print(result)  # Output the Prometheus-compatible metric

if __name__ == "__main__":
    asyncio.run(test_http_call_latency())
