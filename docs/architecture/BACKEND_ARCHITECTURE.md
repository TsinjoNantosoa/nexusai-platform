# Backend architecture

NexusAI uses a modular monolith. FastAPI owns HTTP composition and OpenAPI; routers delegate to domain services; SQLAlchemy models are persisted through PostgreSQL; Alembic owns schema changes. The modules are `auth`, `users`, `wallet`, `billing`, and `api`.

The API is versioned under `/api/v1`. Health endpoints remain at `/health/live` and `/health/ready`. Request IDs are generated or propagated through `X-Request-ID`, returned in the response, and included in structured logs. Unexpected errors return a generic `internal_error` without stack traces.

The local Compose backend is non-root and depends on the PostgreSQL healthcheck. Redis, microservices, Stripe, and AI providers are intentionally deferred.
