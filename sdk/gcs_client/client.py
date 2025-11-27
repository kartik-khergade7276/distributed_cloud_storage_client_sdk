
import asyncio, time
from typing import Any, Dict, List, Optional
import httpx


class StorageClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 10.0,
                 max_retries: int = 3, backoff_factor: float = 0.3) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self._client = httpx.AsyncClient(timeout=self.timeout)
        self.metrics: Dict[str, Any] = {"requests_total": 0, "requests_failed": 0, "latencies_sec": []}

    async def close(self) -> None:
        await self._client.aclose()

    async def _request_with_retries(self, method: str, path: str, **kwargs) -> httpx.Response:
        url = f"{self.base_url}{path}"
        attempt = 0
        last_exc: Optional[Exception] = None
        while attempt <= self.max_retries:
            start = time.perf_counter()
            try:
                self.metrics["requests_total"] += 1
                resp = await self._client.request(method, url, **kwargs)
                self.metrics["latencies_sec"].append(time.perf_counter() - start)
                if resp.status_code >= 500:
                    raise httpx.HTTPStatusError("server error", request=resp.request, response=resp)
                return resp
            except Exception as exc:
                last_exc = exc
                self.metrics["requests_failed"] += 1
                attempt += 1
                if attempt > self.max_retries:
                    raise
                await asyncio.sleep(self.backoff_factor * attempt)
        raise last_exc  # type: ignore[misc]

    async def health(self) -> Dict[str, Any]:
        return (await self._request_with_retries("GET", "/health")).json()

    async def create_bucket(self, bucket: str) -> Dict[str, Any]:
        return (await self._request_with_retries("POST", f"/buckets/{bucket}")).json()

    async def list_buckets(self) -> List[str]:
        return (await self._request_with_retries("GET", "/buckets")).json()

    async def list_objects(self, bucket: str) -> Dict[str, Any]:
        return (await self._request_with_retries("GET", f"/objects/{bucket}")).json()

    async def put_object(self, bucket: str, object_name: str, data: str) -> Dict[str, Any]:
        payload = {"bucket": bucket, "object_name": object_name, "data": data}
        return (await self._request_with_retries("POST", "/objects", json=payload)).json()

    async def get_object(self, bucket: str, object_name: str) -> str:
        payload = {"bucket": bucket, "object_name": object_name}
        return (await self._request_with_retries("POST", "/objects/get", json=payload)).json()["data"]

    def summarize_metrics(self) -> Dict[str, Any]:
        lats = self.metrics["latencies_sec"]
        if not lats:
            avg = p95 = 0.0
        else:
            avg = sum(lats) / len(lats)
            sl = sorted(lats)
            p95 = sl[int(0.95 * (len(sl) - 1))]
        return {
            "requests_total": self.metrics["requests_total"],
            "requests_failed": self.metrics["requests_failed"],
            "avg_latency_sec": round(avg, 4),
            "p95_latency_sec": round(p95, 4),
        }
