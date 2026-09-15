# Current Development Status

Last updated: 2026-09-15 (WIB)
Owning branch / next IDE workspace: `Codex`
User requested synchronization of `main`, `GPT`, and `Codex` after this update.

## Fresh ingestion evidence (2026-09-15 late WIB)

Operator supplied fresh PostgreSQL exports from `public.market_data_batches` and
`public.candles` after market activity resumed.

- Latest 30 batch rows cover sequence 499 through 528 with no missing sequence values.
- Batch record counts in that sample: 25 batches with 32 records, 3 with 15 records,
  1 with 25 records, and 1 with 3 records. Partial batches are not treated as an
  error by themselves.
- The supplied candle export contains 50 rows from 11:15 through 23:30 WIB, each
  spaced exactly 15 minutes apart, with no duplicate open times and no internal
  gaps in that sample.
- OHLC invariants in the supplied 50-row sample are valid: High is not below
  Open/Close, Low is not above Open/Close, and High is not below Low.
- This is direct evidence that the current antix ingestion path reached database
  persistence for the sampled data; it replaces the earlier "live persistence
  pending" status for that sample window.
- The candle export does not include instrument/timeframe columns, so this evidence
  must not be generalized to all 15 canonical series. A full 5 instruments x
  M15/H1/H4 audit is still required before declaring market-data recovery complete.

## Git/frontend checkpoint (2026-09-15)

- Integrated remote commits through 7c99d2c: Angular operations dashboard,
  PostgreSQL-backed login, users SQL and database-generated user UUIDs.
- Added the frontend npm lockfile and disabled Angular CLI analytics from the
  existing local changes. Lockfile root dependencies match package.json.
- Verified `cd frontend && npm run build` successfully and `git diff --check`.
  Backend changes already committed upstream were not retested in this sync.
- Next: verify database login/dashboard against the deployed API. For an existing
  users table, check the id default before rollout: SQL 014 uses CREATE TABLE IF
  NOT EXISTS and does not alter an existing table's default.

## Recovery checkpoint (last observed 2026-09-13)

Phase 02 operational hardening. Target is antiX Linux with runit. PostgreSQL,
published .NET API and Python bridge run on the server. Prior API published-release
activation, restart/reboot and manual binary rollback were verified.

Exporter metadata 1.062 is running on the target. Earlier Experts evidence showed
successful initialization with `source=antix-mt5-primary`, `nextSequence=478`,
followed by `reason=QUOTE_STALE expectedOffset=10800`. That earlier readiness block
has now been followed by fresh database persistence evidence on September 15.
Do not disable the clock guard or reset sequence. Heartbeat alone remains
insufficient proof of candle readiness.

## Completed recovery on target

- XAUUSD H1: scripts 012 and 013 recovered 16 + 15 = 31 broker CSV candles.
  Operator COUNT confirmed the first 16; subsequent diagnostics rose from 50 to
  65 candles after the second repair, with internal absent slots falling 19 -> 4.
  The four remaining slots (September 10/11 03:00–04:00 WIB) also lack bars in
  the supplied broker export. Do not synthesize bars or generalize this into a
  universal trading-session rule. Window totals change as the lookback advances.
- Scoped UTC+3 mapping matches broker CSV samples. One quarantine tick volume was
  3752 versus current CSV 3750; repair 012 uses CSV 3750. Cause remains unknown.
  Manual SQL repairs do not rewrite batch ledger, checkpoints or quarantine.
- EURUSD H1 checkpoint candle and all nine supplied H1 CSV bars matched DB at
  UTC+3. M15 checkpoint and two neighboring bars also matched OHLC/tick volume.
  Operator was guided to change only antix EURUSD M15/H1 `.Offset` 0 -> 10800;
  reattachment succeeded. Full cross-series backfill verification is still pending.
  Keys: M15 `8fcb81b4ff69b176a441e5bd` (.Time 1789006500),
  H1 `d17be2b0932493d3b30c1906` (.Time 1789002000).
- Deleting/recloning the server repository removed `.venv` and spool. Recreated
  Python environment and restored the 851-pair quarantine archive. The later
  13 envelopes from the old lubuntu producer were outside that archive; no full
  recovery of those additional payloads is claimed. Database was not restored.
- External spool migration applied successfully: 1702 files copied and verified
  to `/var/lib/forex-intelligence/spool`, launcher switched, source retained.
  Backup: `/var/lib/forex-intelligence/spool-migration-6o2dcf4r` (launcher/manifest).
  After restart: bridge HEALTHY, antix heartbeat HEALTHY, pending 0, quarantine 851.
  Code and `.venv` remain inside the checkout; use git pull, not delete/reclone.
- Operator reports a new database backup after the 31-candle recovery. Exact path
  and restore integrity of that new backup have not been independently verified.

## Incident evidence and preserved state

Ledger antix sequence 1 dates from September 5. September 11 logs restarted at
nextSequence 1 despite existing ledger entries. Ledger/quarantine sequence 118
has different batch IDs/checksums. Root cause of state rollback/reuse remains
unproven. Old 0.5 source defaulting to lubuntu was later found in the active MT5
folder. Sequence variables last observed before the new sample: antix 477, legacy
lubuntu 15. Do not replay conflicting HTTP 409 envelopes unchanged or rename
historical ledger rows.

Original backups: `~/forex-recovery-backups/quarantine-20260912-213012.tar.gz`
(gzip verified), `gvariables-20260912-213103.dat`, and the pre-recovery Custom
PostgreSQL dump in `~/Dokumen` (archive listing checked, restore not tested).
Do not restore that pre-recovery DB dump over the repaired database.

## Verification and limits

Local checks at code checkpoint dd15888: 84 bridge tests and 9 tool tests passed;
runit shell syntax and git diff whitespace checks passed. Guard tests execute
actual exporter function bodies with simulated C++ adapters, not native Wine.
Both SQL repairs were tested on isolated PostgreSQL with canonical candle schema:
dry-run rollback, successful insertion, idempotent repeats and conflict refusal.

Remaining: audit all 15 canonical series; verify EURUSD M15/H1 backfill against
repaired checkpoints; confirm current heartbeat/backlog/quarantine state; run
controlled restart/lock/failure tests of the guards; historical DST normalization
and broker-session calibration; remaining Phase 02 scope (tick/spread, account
telemetry, observability, dashboard WAIT, operations runbook and five-trading-day
target soak). No Phase 03 completion claim.
