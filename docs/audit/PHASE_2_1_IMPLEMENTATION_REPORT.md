# Phase 2.1 implementation report

Date: 2026-11-26
Branch: `feat/backend-foundation`
Baseline: `4e4b2d4` (`docs: record Phase 2 architecture and quality gates`)

## Corrections delivered

- Added PostgreSQL-backed tests for session expiry, session/CSRF rotation, all invalid-CSRF variants, origin rejection, cross-account ownership, deterministic rate limiting, forwarded-header bypass resistance, and recovery.
- Added PostgreSQL-backed tests for welcome replay, authorized internal credit, duplicate and contradictory wallet references, partial/full/concurrent refunds, and the explicit `balance == SUM(entries)` invariant.
- Added fail-closed production configuration validation for secure cookies, explicit HTTPS origins, explicit trusted hosts, supported SameSite values, positive session lifetime, and positive authentication limiter settings.
- Added pinned development-only `pip-audit==2.10.1`; targeted backend dependency corrections remove the findings reported against the previous pins.
- Replaced hardcoded `python3` in the browser wrapper with `sys.executable`; added independent responsive viewport-group selection without changing application behavior.
- Updated Phase 2 reports, architecture/security documentation, README guidance, and created the four required Phase 2.1 reports.

## Scope preserved

The authoritative `frontend/docs/CAHIER_DES_CHARGES.md` was not modified. Stripe, AI, production deployment, and public publication remain outside this phase.
