# Next Tasks

Tasks are ordered by current priority. Agents should compare `GPT` and `Codex` before starting an item.

## Immediate recovery checkpoint (2026-09-12)

User requested synchronization of `main`, `GPT`, and `Codex`; continue IDE work on
`Codex`. Initial native compile produced 0 errors and 1 version-format warning;
`0.600` retained the warning; metadata now `1.060`, awaiting recompile. Runtime activation remains unverified.

- [x] Investigate September 11 sequence reuse and collect backup evidence (see CURRENT-STATUS).
- [x] Implement exporter 0.6 startup/sequence guards and read-only recovery inventory locally.
- [x] Compile initial 0.6 in MetaEditor (0 errors, 1 version-format warning).
- [ ] Recompile `1.060` metadata fix; verify native lock, restart and readiness on antiX.
- [ ] Review current ledger/spool/quarantine/state maximum and current broker offset for activation.
- [ ] Validate quarantine candidates against DB/broker; resolve offset-0 checkpoints and design
      broker-history extraction/recovery batches. Do not replay HTTP 409 envelopes unchanged.
- [ ] Verify all 15 series after controlled recovery and then recalibrate broker sessions.

Instructions and limitations: `mt5-exporter/RECOVERY.md`. Historical task entries below remain history.

1. [x] Build a Python MT5 simulator/dummy sender using the exact `mt5-heartbeat.v1`, `mt5-envelope.v1`, and `candle.v1` contracts.
2. [x] Support a normal local scenario that sends heartbeat plus one valid EURUSD H1 FINAL candle to the running Python bridge.
3. [x] Add deterministic simulator scenarios for duplicate batch, invalid OHLC, and heartbeat disconnect/staleness.
4. [x] Add tests for simulator payload generation where useful; default tests do not require a live broker.
5. [x] Use the simulator to verify duplicate handling, invalid-OHLC rejection, terminal health transitions, recovery, and spool depth locally.
6. [x] Harden the durable spool with restart recovery, idempotency/sequence conflict handling, quarantine, ACK-driven publisher behavior, retry/backoff, and structured secret-safe logging tests.
7. [x] Run and record a bounded local soak/load simulation of receiver, spool, replay, and recovery behavior.
8. [x] Replace the simulator with the real MQL5 exporter and verify the first EURUSD H1 FINAL candle through Python validation and durable spool on the demo terminal.
9. [x] Expand exporter and simulator contract coverage to M15/H1/H4 and the five canonical instruments.
10. [x] Confirm with the user that the real MT5 server-laptop boundary is operational and Python acquisition is ready to hand off to .NET development.
11. [x] Add a compatible idempotent .NET batch-ingestion endpoint, machine authentication, PostgreSQL batch ledger, and wire the tested publisher into the bridge runtime.
12. [x] Apply the new migration and configure the shared bridge API key on the target machines without committing the secret.
13. [x] Verify MT5 -> Python spool -> authenticated .NET ingestion -> PostgreSQL, including backend outage/recovery and the complete real 15-combination acquisition matrix.
14. [x] Add a portable interactive Windows setup script and placeholder configuration template so development secrets can be recreated safely on each laptop.
15. [x] Define and implement idempotent candle-overlap handling for new batches before adding checkpoint/backfill; cover mixed existing/new candle batches with PostgreSQL integration tests.
16. [x] Compile exporter version 0.4 and verify persistent sequence continuity plus duplicate-safe delivery after EA/terminal restart on the target server.
17. [x] Design and implement durable per-instrument/timeframe checkpoints with bounded chronological candle backfill after restart or reconnect.
18. [x] Compile exporter version 0.5 and verify checkpoint catch-up after a short target-terminal outage that does not cross a broker UTC-offset transition.
19. [ ] Design broker-aware historical timezone/DST normalization before supporting backfill across an offset transition.
20. [x] Implement deterministic per-series freshness and recent gap detection with explicit weekend market-closed handling.
21. [ ] Verify `GET /api/market-data/status` against target PostgreSQL and calibrate the canonical UTC weekly session window to the selected broker.
    EURUSD/XAUUSD session screenshots collected on 2026-09-10; current broker UTC+3 is inferred
    from clock screenshots. Next: inspect XAUUSD H1 gaps in DBeaver with WIB output and compare
    against broker sessions/history before changing the fixed schedule. Use Asia/Jakarta for
    human-readable output while preserving UTC storage/API contracts. Run the prepared read-only
    `database/010-diagnose-xauusd-h1-gaps.sql` (instructions in `database/README.md`). It compares
    current API counts with the fixed UTC+3 XAUUSD session hypothesis; no target query results yet.
22. [x] Add managed Lubuntu `systemd` startup templates/installer with external secret files, plus a read-only quarantine audit tool.
23. [x] Replace the Lubuntu-specific managed-startup path with one compatible with the target
    antiX init system, then install and reboot-verify PostgreSQL/API/bridge startup after safely
    transferring the existing local secrets.
24. [x] Expand the exporter source policy test to reject direct order APIs, `CTrade` methods,
    trade request primitives, and trading action constants.
25. [x] Replace the runit API command from source-based `dotnet run` to a versioned
    `dotnet publish` release artifact with atomic activation, health verification, and rollback.
    Tooling implemented on 2026-09-08; local publish, syntax, and six isolated recovery scenarios
    passed. Target migration, API restart, reboot, and manual rollback verified on 2026-09-09/10.
    First activation ready in 5s, rollback in 3s; verifier PASS, terminal HEALTHY, spool 0, quarantine
    493. Exact restart/boot readiness and nonzero backlog drain time were not measured. Both releases
    use the same source revision. Next: investigate remaining gaps and calibrate broker sessions.

Local PostgreSQL migration plus simulator -> bridge -> .NET -> PostgreSQL happy-path,
duplicate-ACK, and backend outage/recovery verification completed on 2026-08-28. The dedicated
Linux server repeated the schema, authentication, persistence, and outage/replay path on
2026-08-29. Exporter version 0.3 subsequently stored the complete real five-instrument by
three-timeframe matrix. The next hardening checkpoint is restart-safe exporter sequence state;
version 0.4 was verified with ledger sequences continuing through 212, active spool depth zero,
and quarantine depth zero. Exporter version 0.5 ACK-gated checkpoint catch-up was then verified
after a short target-terminal outage without crossing a broker UTC-offset transition. The next
operational checkpoint is now gap investigation and target broker calibration of the market-data
status endpoint; published release deployment and manual rollback have passed on antiX.

Do not start Python -> .NET publishing merely because it is later in Phase 02; finish and verify the MT5/Python acquisition boundary first.
