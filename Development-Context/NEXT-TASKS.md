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
12. [ ] Apply the new migration and configure the shared bridge API key on the target machines without committing the secret.
13. [ ] Verify MT5 -> Python spool -> authenticated .NET ingestion -> PostgreSQL, including duplicate ACK and backend outage/recovery.

Do not start Python -> .NET publishing merely because it is later in Phase 02; finish and verify the MT5/Python acquisition boundary first.
