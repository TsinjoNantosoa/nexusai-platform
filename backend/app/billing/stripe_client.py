from collections.abc import Callable, Iterator, Mapping
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


def normalize_stripe_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): normalize_stripe_value(item) for key, item in value.items()}
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return normalize_stripe_value(to_dict())
    if isinstance(value, list | tuple):
        return [normalize_stripe_value(item) for item in value]
    return value


def normalize_stripe_resource(
    resource: Any,
    *,
    operation: str,
    deserialize: Callable[..., Any] | None = None,
    expected_object: str | None = None,
) -> dict[str, Any]:
    try:
        if isinstance(resource, stripe.StripeResponse):
            if deserialize is None:
                raise ValueError("A Stripe deserializer is required for raw responses.")
            resource = deserialize(resource, api_mode="V1")
        normalized = normalize_stripe_value(resource)
        if not isinstance(normalized, dict):
            raise ValueError("Stripe response is not an object.")
        resource_id = normalized.get("id")
        if not isinstance(resource_id, str) or not resource_id:
            raise ValueError("Stripe response has no identifier.")
        object_type = normalized.get("object")
        if expected_object and object_type is not None and object_type != expected_object:
            raise ValueError("Stripe response object type is unsupported.")
        return normalized
    except StripeClientError:
        raise
    except Exception:
        raise StripeClientError(operation, "response_invalid") from None


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

    def retrieve_product(self, product_id: str) -> Mapping[str, Any]: ...

    def retrieve_price(self, price_id: str) -> Mapping[str, Any]: ...

    def create_customer(
        self, params: Mapping[str, Any], idempotency_key: str
    ) -> Mapping[str, Any]: ...

    def retrieve_customer(self, customer_id: str) -> Mapping[str, Any]: ...

    def create_checkout_session(
        self, params: Mapping[str, Any], idempotency_key: str
    ) -> Mapping[str, Any]: ...

    def retrieve_checkout_session(self, session_id: str) -> Mapping[str, Any]: ...

    def list_checkout_session_line_items(self, session_id: str) -> Iterator[Mapping[str, Any]]: ...


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
        return self._normalized_request(
            "account",
            lambda: self._client.raw_request("get", "/v1/account"),
            expected_object="account",
        )

    def list_products(self) -> Iterator[Mapping[str, Any]]:
        listing = self._request(
            "product discovery", lambda: self._client.v1.products.list({"limit": 100})
        )
        return self._iterate(
            "product discovery",
            listing,
            expected_object="product",
            deserialize=self._client.deserialize,
        )

    def create_product(self, params: Mapping[str, Any], idempotency_key: str) -> Mapping[str, Any]:
        return self._normalized_request(
            "product creation",
            lambda: self._client.v1.products.create(
                dict(params), {"idempotency_key": idempotency_key}
            ),
            expected_object="product",
        )

    def list_prices(self) -> Iterator[Mapping[str, Any]]:
        listing = self._request(
            "price discovery", lambda: self._client.v1.prices.list({"limit": 100})
        )
        return self._iterate(
            "price discovery",
            listing,
            expected_object="price",
            deserialize=self._client.deserialize,
        )

    def create_price(self, params: Mapping[str, Any], idempotency_key: str) -> Mapping[str, Any]:
        return self._normalized_request(
            "price creation",
            lambda: self._client.v1.prices.create(
                dict(params), {"idempotency_key": idempotency_key}
            ),
            expected_object="price",
        )

    def retrieve_product(self, product_id: str) -> Mapping[str, Any]:
        return self._normalized_request(
            "product retrieval",
            lambda: self._client.v1.products.retrieve(product_id),
            expected_object="product",
        )

    def retrieve_price(self, price_id: str) -> Mapping[str, Any]:
        return self._normalized_request(
            "price retrieval",
            lambda: self._client.v1.prices.retrieve(price_id),
            expected_object="price",
        )

    def create_customer(self, params: Mapping[str, Any], idempotency_key: str) -> Mapping[str, Any]:
        return self._normalized_request(
            "customer creation",
            lambda: self._client.v1.customers.create(
                dict(params), {"idempotency_key": idempotency_key}
            ),
            expected_object="customer",
        )

    def retrieve_customer(self, customer_id: str) -> Mapping[str, Any]:
        return self._normalized_request(
            "customer retrieval",
            lambda: self._client.v1.customers.retrieve(customer_id),
            expected_object="customer",
        )

    def create_checkout_session(
        self, params: Mapping[str, Any], idempotency_key: str
    ) -> Mapping[str, Any]:
        return self._normalized_request(
            "Checkout Session creation",
            lambda: self._client.v1.checkout.sessions.create(
                dict(params), {"idempotency_key": idempotency_key}
            ),
            expected_object="checkout.session",
        )

    def retrieve_checkout_session(self, session_id: str) -> Mapping[str, Any]:
        return self._normalized_request(
            "Checkout Session retrieval",
            lambda: self._client.v1.checkout.sessions.retrieve(session_id),
            expected_object="checkout.session",
        )

    def list_checkout_session_line_items(self, session_id: str) -> Iterator[Mapping[str, Any]]:
        listing = self._request(
            "Checkout Session line-item retrieval",
            lambda: self._client.v1.checkout.sessions.line_items.list(session_id, {"limit": 100}),
        )
        return self._iterate(
            "Checkout Session line-item retrieval",
            listing,
            expected_object="item",
            deserialize=self._client.deserialize,
        )

    @staticmethod
    def _iterate(
        operation: str,
        listing: Any,
        expected_object: str,
        deserialize: Callable[..., Any],
    ) -> Iterator[Mapping[str, Any]]:
        try:
            try:
                iterator = listing.auto_paging_iter()
            except AttributeError:
                iterator = iter(listing)
            for resource in iterator:
                yield normalize_stripe_resource(
                    resource,
                    operation=operation,
                    deserialize=deserialize,
                    expected_object=expected_object,
                )
        except StripeClientError:
            raise
        except Exception as error:
            raise StripeClientError(operation, _stripe_error_code(error)) from None

    def _normalized_request(
        self,
        operation: str,
        request: Callable[[], Any],
        *,
        expected_object: str,
    ) -> Mapping[str, Any]:
        try:
            return normalize_stripe_resource(
                request(),
                operation=operation,
                deserialize=self._client.deserialize,
                expected_object=expected_object,
            )
        except StripeClientError:
            raise
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
