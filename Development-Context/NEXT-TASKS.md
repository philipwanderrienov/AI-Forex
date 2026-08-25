# Next Tasks

Tasks are ordered by current priority. Agents should compare `GPT` and `Codex` before starting an item.

1. Build a Python MT5 simulator/dummy sender using the exact `mt5-heartbeat.v1`, `mt5-envelope.v1`, and `candle.v1` contracts.
2. Support a normal local scenario that sends heartbeat plus one valid EURUSD H1 FINAL candle to the running Python bridge.
3. Add deterministic simulator scenarios for duplicate batch, invalid OHLC, and heartbeat disconnect/staleness.
4. Add tests for simulator payload generation where useful; default tests must not require a live broker.
5. Use the simulator to verify terminal health transitions and spool depth locally.
6. When the server laptop is ready, replace the simulator with the real MQL5 exporter for the first EURUSD H1 end-to-end test.
7. Only after that milestone succeeds, expand exporter coverage to M15/H1/H4 and then the five canonical instruments.

Do not start Python -> .NET publishing merely because it is later in Phase 02; finish and verify the MT5/Python acquisition boundary first.
