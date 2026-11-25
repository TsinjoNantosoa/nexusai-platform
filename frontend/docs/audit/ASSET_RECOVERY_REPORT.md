# Character asset recovery report

Date: 2026-11-25

## Method

The four existing public preview URLs from the asset descriptors were requested directly over HTTPS without credentials. Each returned an image response and was copied into the repository as a local WebP under `public/assets/characters/`.

## Results

| Character | Runtime file |
| --- | --- |
| Atlas | `public/assets/characters/atlas.webp` |
| Echo | `public/assets/characters/echo.webp` |
| Luna | `public/assets/characters/luna.webp` |
| Nova | `public/assets/characters/nova.webp` |

The JSON descriptors retain the original asset IDs and source URLs as provenance, but runtime `url` values are local. No browser request to `/__l5e/` is required by the application.

## Limitation

The preview host is project-owned/publicly accessible in this environment, but its licensing terms were not independently verified. Confirm ownership and redistribution rights before a public release.
