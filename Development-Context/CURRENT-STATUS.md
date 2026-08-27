# Current Development Status

Last updated: 2026-08-27
Owning branch for this update: `Codex`

## Current focus

Phase 02 market-data acquisition. Development is intentionally focused on the MT5/MQL5 exporter and Python bridge before moving into .NET ingestion.

## Implemented

- Python bridge runs locally on `127.0.0.1:8001`.
- `GET /health` reports bridge, terminal heartbeat freshness, and durable spool health.
- MT5 heartbeat contract and receiver are implemented.
- Candle envelope validation is implemented for canonical instruments EURUSD, GBPUSD, EURGBP, EURCHF, and XAUUSD and timeframes M15, H1, and H4.
- Candle validation includes UTC timestamps, OHLC rules, final/partial status, tick volume, batch size, and SHA-256 checksum.
- Durable FIFO spool includes duplicate protection, item/byte capacity limits, and disk-free monitoring.
- Unit tests exist for contracts, health, server, and spool.
- MQL5 exporter on the GPT lineage has been upgraded from heartbeat-only to a first real `EURUSD H1` FINAL-candle export using `CopyRates`, posting to `/v1/mt5/envelopes`.
- Development-only `mt5-bridge/tools/mt5_simulator.py` sends the same heartbeat and `EURUSD H1` candle contracts as the real exporter using only Python standard-library dependencies.
- Simulator supports continuous heartbeat, `--once`, duplicate-batch, invalid-OHLC, and disconnect scenarios.
- Simulator payload generation is covered by unit tests for heartbeat and valid H1 contracts, ULID shape, reusable duplicate batch IDs, and invalid-OHLC rejection with a valid checksum.
- Durable spool recovery, exact-duplicate detection, batch/sequence conflict detection, corrupt-entry quarantine, and permanent backend rejection quarantine are implemented.
- A backend publisher component supports ACK-driven removal and bounded retry with exponential backoff and jitter. It is unit-tested but not yet wired into the bridge runtime or a compatible .NET batch-ingestion endpoint.
- Structured JSON logging and recursive secret redaction are implemented.
- The receiver returns `202 duplicate` for an identical retry, `409 batch_id_conflict` for conflicting batch reuse, `409 sequence_conflict` for conflicting source sequence reuse, and `507 spool_full` when capacity is exhausted.
- The MQL5 exporter formats heartbeat and candle timestamps as canonical ISO-8601 UTC (`YYYY-MM-DDTHH:MM:SSZ`) rather than the dotted display format returned by `TimeToString`.
- The MQL5 WebRequest timeout is configurable and defaults to 5000 ms, with diagnostic logging for non-2xx responses. This follows intermittent `status=1003` observations on the real MT5/Wine terminal with the earlier 1000 ms timeout.
- The Python receiver now responds with HTTP/1.1 so MT5/Wine can complete `Expect: 100-continue` negotiation for the larger candle envelope. Real-terminal evidence showed heartbeats reaching the handler while envelope requests timed out with status 1003 before any envelope event was logged under HTTP/1.0.

## Locally verified by user

On 2026-08-27, the real MT5 demo terminal on the dedicated server laptop successfully reached
the native Python bridge through the MQL5 exporter. After enabling algorithmic trading and
allowing `http://127.0.0.1:8001` under MT5 `Tools -> Options -> Experts`, `GET /health`
reported terminal status `HEALTHY`. This verifies the real MT5 -> MQL5 -> Python heartbeat
boundary.

The first real `EURUSD H1` FINAL-candle milestone also completed successfully on the
MetaQuotes demo server. After correcting the account/server configuration, refreshing current
broker history, increasing the MQL5 request timeout, and enabling HTTP/1.1 for MT5/Wine
`Expect: 100-continue` compatibility, the EA logged `Published FINAL EURUSD H1 candle`.
The bridge accepted the envelope, stored it in the dedicated durable spool, and did not add
repeated copies of the same final candle. The user confirmed the stored candle data matched
the intended current H1 test.

The MT5 simulator happy path has now been verified successfully on the user's Mac development machine.

After running the bridge and simulator, `GET /health` returned:

- bridge `status`: `HEALTHY`
- terminal `status`: `HEALTHY`
- terminal `sourceInstanceId`: `mt5-simulator-local`
- spool `status`: `AVAILABLE`
- spool `depth`: `1`
- spool `usedBytes`: `692`

This proves the local dummy pipeline works end-to-end for heartbeat plus one valid `EURUSD H1` FINAL candle: simulator -> HTTP bridge -> contract/checksum validation -> durable spool.

The earlier Windows bridge-only verification also succeeded: before a producer was connected, `/health` correctly reported terminal `UNKNOWN`, spool `AVAILABLE`, and depth `0`.

## Locally verified by Codex

On 2026-08-25, the simulator failure/recovery path was verified against a live local bridge using an isolated temporary spool:

- The duplicate scenario returned `202 accepted` for the first envelope and `202 duplicate` for the second; spool depth remained 1.
- The invalid-OHLC scenario returned `400 invalid_ohlc`; spool depth remained 1.
- With no new heartbeat, terminal health transitioned from `HEALTHY` to `WARNING` after 10 seconds and `STALE` after 20 seconds.
- A new valid heartbeat returned `202 accepted` and immediately restored terminal health to `HEALTHY`; spool depth remained 1.

The temporary bridge process was stopped and its isolated test spool was removed after verification.

## Latest automated verification

On 2026-08-27:

- `PYTHONPATH=src python3 -m unittest discover -s tests -v` completed successfully with 70 tests passing from `mt5-bridge/` after the enqueue and HTTP/1.1 regressions were covered.
- `dotnet restore ForexIntelligence.sln`, `dotnet build ForexIntelligence.sln --no-restore`, and `dotnet test ForexIntelligence.sln --no-build --no-restore` completed successfully with 21 tests passing and no build warnings.
- `dotnet format ForexIntelligence.sln --verify-no-changes --no-restore` completed successfully.

## Local soak/load verification

On 2026-08-27, `tools/bridge_soak_test.py` completed a bounded temporary-spool run with:

- 500 accepted envelopes and 50 verified idempotent duplicate retries;
- receiver health depth matching all accepted envelopes before restart;
- all 500 pending envelopes recovered after reopening the spool;
- one deterministic transient backend failure retried and then acknowledged;
- 499 envelopes acknowledged, one deterministic permanent rejection quarantined, and zero pending envelopes after replay;
- 501 publisher calls completed in 16.57 seconds end-to-end (33.25 HTTP requests/second during the combined run).

The temporary server was stopped and its spool was automatically removed after verification.

## Not yet verified

- Real M15/H4 export and the remaining canonical instruments.
- Real terminal/bridge disconnect, restart, and recovery behavior.
- The publisher is not connected to the bridge runtime, machine authentication, or a compatible idempotent .NET batch-ingestion endpoint.
