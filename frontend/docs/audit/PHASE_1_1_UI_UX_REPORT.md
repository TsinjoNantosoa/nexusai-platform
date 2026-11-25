# Phase 1.1 UI/UX implementation report

Date: 2026-11-25
Branch: `feat/frontend-stabilization`

## Root causes

- The public header rendered desktop navigation and three actions without a mobile interaction model.
- Mobile hero typography used a fixed 61px title, while facts and actions remained horizontal.
- Character and pricing grids kept two columns too long for narrow phones.
- Authenticated header controls had no compact language treatment at 280–320px.
- Chat flex children lacked explicit minimum-height/min-width constraints for scrolling and keyboard-sized viewports.
- Browser autofill could replace the dark input surface with a light platform color.

## Corrections

- Added an accessible public mobile menu with focus capture, focus restoration, Escape support, close-on-navigation, a modal backdrop, and 44px touch targets in `src/components/layout/Shell.tsx`.
- Added fluid mobile hero typography, full-width stacked CTAs, wrapped facts, single-column narrow grids, and safe-area-aware bottom navigation in `src/styles.css`.
- Added compact authenticated header language controls and chat flex sizing for mobile keyboards.
- Added dark autofill styling for email/password controls.
- Added local character WebP files to the approved PWA precache; build size increased from 44 entries/789.88 KiB to 48 entries/1109.25 KiB.
- No business rules, prices, translations, character artwork, or API boundaries were changed.

## Scope limits

The visual check is automated Chromium layout/interaction evidence, not a pixel-diff certification. Physical Android/iOS installation, assistive technology certification, and production device keyboard behavior remain untested.
