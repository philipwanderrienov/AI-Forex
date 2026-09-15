# Next Tasks

Updated: 2026-09-15 (WIB). IDE work continues on `Codex`.
Fetch and compare `main`, `GPT`, and `Codex` before development.
Canonical phase contracts remain in Development-Phases; evidence is in CURRENT-STATUS.

## Frontend/login follow-up

- [x] Integrate upstream changes through 7c99d2c and track frontend npm lockfile.
- [x] Disable Angular CLI analytics; frontend production build passes locally.
- [ ] Verify login/dashboard with the deployed API and database; inspect the UUID
  default on existing users tables (SQL 014 does not alter existing tables).

## Fresh ingestion verification

- [x] Confirm fresh database persistence from September 15 exports: sampled batch
  sequences 499-528 are contiguous with no missing values.
- [x] Confirm the supplied 50-row candle sample is internally continuous at 15-minute
  intervals, has no duplicate open times, and passes basic OHLC invariants.
- [ ] Identify the instrument/timeframe represented by that candle export, because
  the supplied CSV does not include those columns.
- [ ] Audit all five instruments x M15/H1/H4 against database/broker history before
  declaring recovery complete; one clean sample does not prove all 15 series.
- [ ] Verify EURUSD M15/H1 backfill crosses the previously repaired checkpoints.
- [ ] Recheck current antix heartbeat, bridge pending backlog, and quarantine count;
  investigate any increase without automatic replay/discard.
- [ ] Run controlled restart and guard-lock/failure tests, verifying sequence continuity
  and no duplicate/conflicting ingestion after restart.

## Completed in this recovery

- [x] Diagnose sequence reuse and collect backups; implement fail-closed guards.
- [x] Fix configuration UI: unconfigured EA stays attached without publishing.
- [x] Deploy specific pause reasons: target 1.062 reports QUOTE_STALE.
- [x] Recover 31 XAUUSD H1 candles from broker CSV with transactional SQL 012/013.
- [x] Compare EURUSD checkpoint candles with DB/broker and guide offset-only repair.
- [x] Restore bridge environment and 851 quarantine pairs after repository deletion.
- [x] Migrate 1702 spool files to /var/lib/forex-intelligence/spool; health/count verified.
- [x] Operator reports database backup after recovery; restore test remains pending.

## Production deployment preparation (personal/private access)

When the application is ready for production on the antiX server, use the private-access
architecture recorded in `DECISIONS.md` rather than publishing the app directly to the internet.

- [ ] Install and configure Tailscale on the antiX server and the user's authorized client devices.
- [ ] Verify the server receives a stable Tailnet identity and can be reached by Tailscale IP;
  optionally enable/test MagicDNS for a friendly private hostname.
- [ ] Build Angular for production with `npm run build`; do not use `ng serve` in production.
- [ ] Install/configure Nginx on antiX to serve the Angular `dist` output at `/`.
- [ ] Configure Nginx `/api/` reverse proxy to the .NET API on an internal loopback endpoint
  such as `127.0.0.1:5204`; keep PostgreSQL and the API port non-public.
- [ ] Ensure the .NET API, Nginx, Tailscale, bridge, and required services survive reboot under
  the antiX-supported service manager/runit arrangement.
- [ ] Review firewall/listening sockets so only the intended local/Tailscale entry points are reachable.
- [ ] Verify login, dashboard/API calls, and market-data views from a laptop/phone on a network
  different from the server's LAN while connected to the same Tailnet.
- [ ] Document production deploy/rollback steps for Angular static assets and Nginx config alongside
  the existing published .NET API release/rollback procedure.
- [ ] Do not add Cloudflare Tunnel, public router port-forwarding, or a paid domain unless the
  application's access model changes from personal/private to public sharing.

## Development backlog after this checkpoint

- Calibrate broker session boundaries using wider evidence. The four observed
  no-bar slots do not establish a universal schedule; SQL 010 remains a hypothesis.
- Design historical timezone/DST normalization before cross-offset backfill.
- Consider published bridge runtime outside the checkout; spool is external now,
  but deleting source/.venv still breaks execution.
- Verify new backup restoration in an isolated database; update recovery runbook.
- Complete Phase 02 tick/spread and read-only account telemetry, decision-data
  observability/dashboard WAIT behavior, and five-trading-day target soak.

Do not rerun already completed repair/initial migration steps as new work.
SQL 012/013 deliberately retain ROLLBACK defaults in Git. Migration refuses an
existing external destination; do not delete it merely to rerun the tool.
