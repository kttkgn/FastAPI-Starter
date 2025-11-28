import asyncio
import logging
from typing import Any, Dict, Optional, Union, NoReturn

import httpx

logger = logging.getLogger(__name__)


class HttpClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 30,
        retries: int = 3,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.retries = retries
        self.headers = headers or {}
        self._client: Optional[httpx.AsyncClient] = None

    def with_base_url(self, base_url: str) -> "HttpClient":
        self.base_url = base_url
        return self

    def with_timeout(self, timeout: int) -> "HttpClient":
        self.timeout = timeout
        return self

    def with_retries(self, retries: int) -> "HttpClient":
        self.retries = retries
        return self

    def with_header(self, key: str, value: str) -> "HttpClient":
        self.headers[key] = value
        return self

    def _build_url(self, endpoint: str) -> str:
        if not self.base_url:
            return endpoint
        return f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

    def _raise_final_error(self, url: str) -> NoReturn:
        raise httpx.HTTPError(f"请求失败（重试{self.retries}次）: {url}")

    async def _request(
        self,
        method: str,
        endpoint: str, **kwargs
    ) -> Dict[str, Any]:
        url = self._build_url(endpoint)
        headers = self.headers.copy()
        headers.update(kwargs.pop("headers", {}))

        retry_exceptions = (
            httpx.ConnectError,
            httpx.ReadTimeout,
            httpx.WriteTimeout,
            httpx.HTTPStatusError
        )

        for attempt in range(self.retries):
            try:
                if not self._client:
                    self._client = httpx.AsyncClient(timeout=self.timeout)

                response = await self._client.request(
                    method=method,
                    url=url,
                    headers=headers, **kwargs
                )
                response.raise_for_status()

                try:
                    data = response.json()
                except ValueError:
                    data = response.text

                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "data": data,
                    "text": response.text
                }

            except retry_exceptions as e:
                logger.warning("请求失败 (%d/%d): %s", attempt + 1, self.retries,
                               str(e))

                if isinstance(e, httpx.HTTPStatusError):
                    if 400 <= e.response.status_code < 500:
                        raise

                if attempt == self.retries - 1:
                    self._raise_final_error(url)

                await asyncio.sleep((attempt + 1) * 0.5)

        self._raise_final_error(url)

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Dict[str, Any]:
        return await self._request("GET", endpoint, params=params, **kwargs)

    async def post(
        self,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], str]] = None, **kwargs
    ) -> Dict[str, Any]:
        json_data = data if isinstance(data, dict) else kwargs.pop("json", None)
        return await self._request(
            "POST", endpoint, json=json_data, data=data if not json_data else None,
            **kwargs
        )

    async def put(
        self,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], str]] = None, **kwargs
    ) -> Dict[str, Any]:
        json_data = data if isinstance(data, dict) else kwargs.pop("json", None)
        return await self._request(
            "PUT", endpoint, json=json_data, data=data if not json_data else None,
            **kwargs
        )

    async def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return await self._request("DELETE", endpoint, **kwargs)

    async def __aenter__(self) -> "HttpClient":
        if not self._client:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
