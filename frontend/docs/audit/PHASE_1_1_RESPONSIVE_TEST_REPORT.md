# Phase 1.1 responsive test report

Date: 2026-11-25

## Command

```sh
bun run test:e2e:responsive
```

The command runs `tests/e2e/responsive_journey.py` against a local Vite dev server. It tests public navigation, Escape/focus menu behavior, local image decoding, direct route navigation, authenticated chat navigation, page errors, and individual overflow offenders.

## Matrix result

| Width | Height | Routes | Document/body overflow | Page errors |
| ---: | ---: | ---: | ---: | ---: |
| 280 | 800 | 13 | 0 / 0 | 0 |
| 320 | 800 | 13 | 0 / 0 | 0 |
| 360 | 800 | 13 | 0 / 0 | 0 |
| 375 | 812 | 13 | 0 / 0 | 0 |
| 390 | 844 | 13 | 0 / 0 | 0 |
| 414 | 896 | 13 | 0 / 0 | 0 |
| 768 | 1024 | 13 | 0 / 0 | 0 |
| 1024 | 900 | 13 | 0 / 0 | 0 |
| 1440 | 1000 | 13 | 0 / 0 | 0 |
| 1920 | 1080 | 13 | 0 / 0 | 0 |

## Screenshots

Ignored local artifacts are written to `browser-artifacts/phase-1-1/<width>/landing.png` and `browser-artifacts/phase-1-1/<width>/chat.png`. They are intentionally not committed.

## Additional checks

- Four local character images decode as WebP at `750x1000`.
- Production preview returned `200` for all application routes, `manifest.webmanifest`, `sw.js`, `offline.html`, and a local portrait.
- No remote Lovable image URL appeared in rendered image sources.
