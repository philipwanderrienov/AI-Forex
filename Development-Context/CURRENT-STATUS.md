# Current Development Status

Last updated: 2026-08-25
Owning branch for this update: `GPT`

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

## Locally verified by user

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

## Next local verification

Continue failure/recovery testing in this order:

1. `python3 tools/mt5_simulator.py --scenario duplicate`
2. `python3 tools/mt5_simulator.py --scenario invalid-ohlc`
3. `python3 tools/mt5_simulator.py --scenario disconnect --disconnect-seconds 15`
4. Verify recovery/reconnect behavior after the disconnect scenario.

Expected goals: duplicate delivery must not create duplicate durable data, invalid OHLC must be rejected by contract validation, and heartbeat loss must transition terminal health away from `HEALTHY` according to freshness thresholds.

## Not yet verified

- Duplicate simulator scenario.
- Invalid-OHLC simulator scenario.
- Disconnect/stale-heartbeat and recovery scenario.
- Real MT5 -> MQL5 -> Python heartbeat.
- Real EURUSD H1 candle -> Python validation -> spool.
- The dedicated server laptop is still being prepared.
- M15/H4 and multi-symbol export are intentionally deferred until the first H1 real-data milestone succeeds.
- Python -> .NET publishing is not the current focus.
