# 06 — Navigation, Visual System, i18n & Offline PWA

## What problem existed
As the app grew across eight views (*Monitor, Band, History, Wellbeing, Assistant, Risks, Link, System*), the interface needed to remain calm, fast on modest hardware, bilingual for English-speaking judges, and installable for offline operation.

## How it was solved
- **Animated sidebar & responsive bar ([BarraLateral.tsx](../../src/app/BarraLateral.tsx), [layout.css](../../src/shared/styles/layout.css), commits `901bc30`, `64c209f`, `b180c0e`):**
  - Collapsible sidebar with a sliding active indicator that adapts into a bottom navigation bar on mobile screens.
  - Removed an overlapping `::after` floating pill on collapsed items while preserving `aria-label` and native `title` accessibility.
- **New silhouette logo ([Logo.tsx](../../src/shared/components/Logo.tsx), commit `b180c0e`):**
  - Integrated the **ORBIT Health** mark (HUD corners, orbit arc, and cardiac pulse) as a transparent silhouette that automatically adapts to light and dark themes.
- **Full ES / EN localization ([i18n](../../src/i18n/index.ts), commits `901bc30`, `feef45a`):**
  - Instant switching between **Spanish** and **English** with a smooth transition modal and per-feature translation files.
- **Consistent visual system & adaptive performance ([ESTILO_PLATAFORMA.md](../ESTILO_PLATAFORMA.md), commit `c9f1081`):**
  - Near-achromatic light/dark palette, *liquid glass* surfaces, clinical traffic-light colors always paired with text, and automatic reduced-effects mode for lower-power devices.
- **Minimal offline PWA ([manifest.webmanifest](../../public/manifest.webmanifest), [sw.js](../../public/sw.js), commit `fc7de22`):**
  - Added app manifest, icon, and a service worker that caches static UI assets **while never caching `/api`**, ensuring clinical data is always fresh from the local server.
