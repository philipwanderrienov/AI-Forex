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
- Development-only `mt5-bridge/tools/mt5_simulator.py` now sends the same heartbeat and `EURUSD H1` candle contracts as the real exporter using only Python standard-library dependencies.
- Simulator supports continuous heartbeat, `--once`, duplicate-batch, invalid-OHLC, and disconnect scenarios.

## Locally verified by user

On Windows development PC, the Python package was installed and the bridge successfully started with:

`py -m forex_intelligence_bridge.server`

`curl.exe http://127.0.0.1:8001/health` returned bridge `HEALTHY`, terminal `UNKNOWN`, spool `AVAILABLE`, and depth `0`. This is expected because a live MT5 terminal has not yet been connected.

## Next local verification

With the bridge running, execute from `mt5-bridge`:

`py tools\mt5_simulator.py --once`

Expected result: heartbeat HTTP 202, candle HTTP 202, terminal becomes `HEALTHY`, and spool depth becomes `1` (assuming an empty spool).

After the happy path succeeds, verify:

- `py tools\mt5_simulator.py --scenario duplicate`
- `py tools\mt5_simulator.py --scenario invalid-ohlc`
- `py tools\mt5_simulator.py --scenario disconnect --disconnect-seconds 15`

## Not yet verified

- Simulator against the user's local running bridge.
- Real MT5 -> MQL5 -> Python heartbeat.
- Real EURUSD H1 candle -> Python validation -> spool.
- The dedicated server laptop is still being prepared.
- M15/H4 and multi-symbol export are intentionally deferred until the first H1 real-data milestone succeeds.
- Python -> .NET publishing is not the current focus.
