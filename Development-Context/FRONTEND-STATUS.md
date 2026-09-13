# Frontend Development Status

Last updated: 2026-09-13 (WIB)
Owning branch for this implementation: `GPT`

## Decisions

- Keep frontend in the existing repository under root `frontend/`; do not create a dedicated frontend branch.
- Angular is the frontend framework.
- Bootstrap handles responsive grid/layout/spacing; PrimeNG + PrimeIcons are the primary application component library.
- Project-specific styling uses SCSS. Lightweight Charts is reserved for trading/candlestick visualizations.
- Operator-facing timestamps are displayed in the browser timezone, expected to be WIB/Asia-Jakarta per the existing presentation decision. API/database canonical timestamps remain UTC.
- Do not bypass backend authentication or exporter safety/recovery controls from the UI.

## Implemented

- Initial standalone Angular application scaffold.
- Responsive financial dashboard shell with sidebar and mobile navigation.
- Bootstrap + PrimeNG/Aura dark-theme integration.
- Login screen wired to `POST /api/auth/login` and bearer-token interceptor.
- Operational overview wired to authenticated `GET /api/system-status` and `GET /api/market-data/status`.
- Market-data table shows all returned canonical series with freshness, last close, age and gap count.
- Development proxy targets the local .NET API at `127.0.0.1:5000`.
- Lightweight Charts dependency is installed but chart UI is intentionally deferred until instrument-history integration is implemented.

## Verification limitation

This change was created through the GitHub workspace and was not executed with Node/npm in the target environment. Run `npm install` and `npm run build` from `frontend/` before treating the scaffold as build-verified. No backend/MT5/database behavior was changed.

## Next

Build-verify the Angular scaffold, correct any package/API compatibility issues, then add refresh-token handling and the first instrument/candlestick view. Keep backend recovery work on its existing path; frontend work must consume stable contracts rather than changing recovery semantics.
