# Next Tasks

Tasks are ordered by current priority. Agents should compare `GPT` and `Codex` before starting an item.

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

Local PostgreSQL migration plus simulator -> bridge -> .NET -> PostgreSQL happy-path,
duplicate-ACK, and backend outage/recovery verification completed on 2026-08-28. The dedicated
Linux server repeated the schema, authentication, persistence, and outage/replay path on
2026-08-29. Exporter version 0.3 subsequently stored the complete real five-instrument by
three-timeframe matrix. The next hardening checkpoint is restart-safe exporter sequence state;
version 0.4 was verified with ledger sequences continuing through 212, active spool depth zero,
and quarantine depth zero. Exporter version 0.5 ACK-gated checkpoint catch-up was then verified
after a short target-terminal outage without crossing a broker UTC-offset transition. The next
checkpoint is target verification and broker calibration of the market-data status endpoint.

Do not start Python -> .NET publishing merely because it is later in Phase 02; finish and verify the MT5/Python acquisition boundary first.
