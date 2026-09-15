# Next Tasks

Updated: 2026-09-15 (WIB). IDE work continues on `Codex`.
Fetch and compare `main`, `GPT`, and `Codex` before development.
Canonical phase contracts remain in Development-Phases; evidence is in CURRENT-STATUS.

## Frontend/login follow-up

- [x] Integrate upstream changes through 7c99d2c and track frontend npm lockfile.
- [x] Disable Angular CLI analytics; frontend production build passes locally.
- [ ] Verify login/dashboard with the deployed API and database; inspect the UUID
  default on existing users tables (SQL 014 does not alter existing tables).
- [ ] Obtain current server ingestion evidence; recovery observations below are
  from September 13 and do not establish current market-data health.

## Completed in this recovery

- [x] Diagnose sequence reuse and collect backups; implement fail-closed guards.
- [x] Fix configuration UI: unconfigured EA stays attached without publishing.
- [x] Deploy specific pause reasons: target 1.062 reports QUOTE_STALE.
- [x] Recover 31 XAUUSD H1 candles from broker CSV with transactional SQL 012/013.
- [x] Compare EURUSD checkpoint candles with DB/broker and guide offset-only repair.
- [x] Restore bridge environment and 851 quarantine pairs after repository deletion.
- [x] Migrate 1702 spool files to /var/lib/forex-intelligence/spool; health/count verified.
- [x] Operator reports database backup after recovery; restore test remains pending.

## Next operational verification: wait for advancing quotes

1. Keep MT5/EA/API/bridge running with antix source and expected offset 10800.
   Latest initialized nextSequence is 478; do not reset sequence or bypass guards.
2. After new quotes and >=30 seconds of stable clock samples, inspect Experts for
   bridge-accepted batches. If paused, use the specific reason to diagnose.
3. Verify new antix batches in public.market_data_batches and actual candles in
   public.candles. HTTP 202 confirms durable bridge acceptance, not backend commit.
4. Check health: antix heartbeat fresh, backlog drains, quarantine remains 851.
   Investigate any increase; do not automatically replay or discard payloads.
5. Verify EURUSD M15/H1 backfill passes the repaired checkpoints. Audit all five
   instruments x M15/H1/H4 against broker history before declaring full recovery.
6. Run controlled restart and guard-lock/failure tests, verifying sequence continuity
   and no duplicates. Successful reattachment alone does not prove all scenarios.

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
