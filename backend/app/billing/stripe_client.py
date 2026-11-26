from collections.abc import Iterator, Mapping
from typing import Any, Protocol

import stripe
from stripe import StripeClient as StripeSdkClient
from stripe._http_client import RequestsClient

from app.core.config import Settings


class StripeClientError(RuntimeError):
    def __init__(self, operation: str, code: str = "stripe_request_failed") -> None:
        self.operation = operation
        self.code = code
        super().__init__(f"Stripe {operation} failed ({code}).")


class StripeGateway(Protocol):
    def account(self) -> Mapping[str, Any]: ...

    def list_products(self) -> Iterator[Mapping[str, Any]]: ...

    def create_product(
        self, params: Mapping[str, Any], idempotency_key: str
    ) -> Mapping[str, Any]: ...

    def list_prices(self) -> Iterator[Mapping[str, Any]]: ...

    def create_price(
        self, params: Mapping[str, Any], idempotency_key: str
    ) -> Mapping[str, Any]: ...


class StripeClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.stripe_enabled:
            raise StripeClientError("initialization", "stripe_disabled")
        if settings.stripe_secret_key is None:
            raise StripeClientError("initialization", "stripe_secret_missing")

        http_client = RequestsClient(timeout=settings.stripe_request_timeout_seconds)
        self._client = StripeSdkClient(
            settings.stripe_secret_key.get_secret_value(),
            stripe_version=settings.stripe_api_version,
            max_network_retries=settings.stripe_max_network_retries,
            http_client=http_client,
        )

    def account(self) -> Mapping[str, Any]:
        return self._request("account", lambda: self._client.raw_request("get", "/v1/account"))

    def list_products(self) -> Iterator[Mapping[str, Any]]:
        listing = self._request(
            "product discovery", lambda: self._client.v1.products.list({"limit": 100})
        )
        return self._iterate("product discovery", listing)

    def create_product(
        self, params: Mapping[str, Any], idempotency_key: str
    ) -> Mapping[str, Any]:
        return self._request(
            "product creation",
            lambda: self._client.v1.products.create(
                dict(params), {"idempotency_key": idempotency_key}
            ),
        )

    def list_prices(self) -> Iterator[Mapping[str, Any]]:
        listing = self._request(
            "price discovery", lambda: self._client.v1.prices.list({"limit": 100})
        )
        return self._iterate("price discovery", listing)

    def create_price(
        self, params: Mapping[str, Any], idempotency_key: str
    ) -> Mapping[str, Any]:
        return self._request(
            "price creation",
            lambda: self._client.v1.prices.create(
                dict(params), {"idempotency_key": idempotency_key}
            ),
        )

    @staticmethod
    def _iterate(operation: str, listing: Any) -> Iterator[Mapping[str, Any]]:
        try:
            iterator = listing.auto_paging_iter()
        except AttributeError:
            iterator = iter(listing)
        try:
            yield from iterator
        except Exception as error:
            raise StripeClientError(operation, _stripe_error_code(error)) from None

    @staticmethod
    def _request(operation: str, request: Any) -> Any:
        try:
            return request()
        except Exception as error:
            raise StripeClientError(operation, _stripe_error_code(error)) from None


def _stripe_error_code(error: Exception) -> str:
    if isinstance(error, stripe.StripeError):
        code = getattr(error, "code", None) or getattr(error, "type", None)
        if isinstance(code, str) and code:
            return code[:80]
    if isinstance(error, TimeoutError | OSError):
        return "network_error"
    return "request_error"
