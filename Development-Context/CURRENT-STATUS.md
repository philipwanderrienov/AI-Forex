# Current Development Status

Last updated: 2026-09-13 (WIB)
Owning branch / next IDE workspace: `Codex`
User requested synchronization of `main`, `GPT`, and `Codex` after this update.

## Current checkpoint

Phase 02 operational hardening. Target is antiX Linux with runit. PostgreSQL,
published .NET API and Python bridge run on the server. Prior API published-release
activation, restart/reboot and manual binary rollback were verified. Current API
and bridge health are healthy; live candle ingestion after this recovery is pending.

Exporter metadata 1.062 is running on the target. Latest Experts screenshot shows
successful initialization with `source=antix-mt5-primary`, `nextSequence=478`,
followed by `reason=QUOTE_STALE expectedOffset=10800`. This confirms the specific
readiness block is an old quote. Do not disable the clock guard or reset sequence.
Wait for advancing broker quotes and at least 30 seconds of stable clock samples,
then verify bridge acceptance AND backend persistence. Heartbeat alone is not
candle readiness. Native 1.062 runtime is observed; a separate compiler summary
for 1.062 was not supplied. Prior 1.060 native compile had zero errors/warnings.

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
  reattachment succeeded, still nextSequence 478. Backfill traversing those
  checkpoints is not yet observed, so end-to-end correction remains unverified.
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
folder. Sequence variables last observed: antix 477, legacy lubuntu 15. Do not
replay conflicting HTTP 409 envelopes unchanged or rename historical ledger rows.

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

Remaining: live ingestion after quote readiness; new batch ledger persistence;
all 15 series audit; controlled restart/lock/failure tests of the new guards;
historical DST normalization and broker-session calibration; remaining Phase 02
scope (tick/spread, account telemetry, observability, dashboard WAIT, operations
runbook and five-trading-day target soak). No Phase 03 completion claim.
