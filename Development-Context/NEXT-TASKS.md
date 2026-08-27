# Next Tasks

Tasks are ordered by current priority. Agents should compare `GPT` and `Codex` before starting an item.

1. [x] Build a Python MT5 simulator/dummy sender using the exact `mt5-heartbeat.v1`, `mt5-envelope.v1`, and `candle.v1` contracts.
2. [x] Support a normal local scenario that sends heartbeat plus one valid EURUSD H1 FINAL candle to the running Python bridge.
3. [x] Add deterministic simulator scenarios for duplicate batch, invalid OHLC, and heartbeat disconnect/staleness.
4. [x] Add tests for simulator payload generation where useful; default tests do not require a live broker.
5. [x] Use the simulator to verify duplicate handling, invalid-OHLC rejection, terminal health transitions, recovery, and spool depth locally.
6. [x] Harden the durable spool with restart recovery, idempotency/sequence conflict handling, quarantine, ACK-driven publisher behavior, retry/backoff, and structured secret-safe logging tests.
7. [x] Run and record a bounded local soak/load simulation of receiver, spool, replay, and recovery behavior.
8. [ ] When the server laptop is ready, replace the simulator with the real MQL5 exporter for the first EURUSD H1 end-to-end test.
9. [ ] Only after that milestone succeeds, expand exporter coverage to M15/H1/H4 and then the five canonical instruments.
10. [ ] After the MT5/Python boundary is proven, add a compatible idempotent .NET batch-ingestion endpoint, machine authentication, and wire the tested publisher into the bridge runtime.

Do not start Python -> .NET publishing merely because it is later in Phase 02; finish and verify the MT5/Python acquisition boundary first.
