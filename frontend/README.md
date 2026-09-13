# Forex Intelligence Frontend

Angular frontend for the Forex Intelligence platform. Frontend code is isolated under this directory; backend, MT5 exporter and bridge remain outside it.

## UI stack

- Angular 20 standalone components
- Bootstrap 5 for responsive layout and spacing
- PrimeNG + PrimeIcons for application components
- SCSS for project-specific visual styling
- Lightweight Charts is installed for the upcoming candlestick view

Bootstrap is used for layout utilities. PrimeNG is the default component library; avoid mixing Bootstrap JS widgets with equivalent PrimeNG components.

## Run locally

```bash
cd frontend
npm install
npm start
```

The development proxy forwards `/api` and `/health` to `http://127.0.0.1:5000`. Change `proxy.conf.json` if the API is bound to another local port.

The current dashboard uses the existing authenticated API endpoints:

- `POST /api/auth/login`
- `GET /api/system-status`
- `GET /api/market-data/status`

Dashboard timestamps are rendered using the browser timezone. The product decision is WIB (`Asia/Jakarta`) for operator-facing displays, while canonical API/database timestamps remain UTC.

## Next frontend work

1. Add token refresh/expiry handling and route-level session recovery.
2. Add instrument detail and candlestick chart using the market-data query endpoint.
3. Add data-quality/recovery views without exposing unsafe replay actions.
4. Add bridge/MT5 operational telemetry only after a supported backend API contract exists.
5. Add AI decision-support views only when validated backend contracts are available.
