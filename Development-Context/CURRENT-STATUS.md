# Current Development Status

Last updated: 2026-08-28
Owning branch for this update: `Codex`

## Current focus

Phase 02 market-data acquisition. The MT5/Python acquisition boundary is complete enough to
move development into authenticated .NET ingestion and PostgreSQL persistence.

## Implemented

- Python bridge runs locally on `127.0.0.1:8001`.
- `GET /health` reports bridge, terminal heartbeat freshness, and durable spool health.
- MT5 heartbeat contract and receiver are implemented.
- Candle envelope validation is implemented for canonical instruments EURUSD, GBPUSD, EURGBP, EURCHF, and XAUUSD and timeframes M15, H1, and H4.
- Candle validation includes UTC timestamps, OHLC rules, final/partial status, tick volume, batch size, and SHA-256 checksum.
- Durable FIFO spool includes duplicate protection, item/byte capacity limits, and disk-free monitoring.
- Unit tests exist for contracts, health, server, and spool.
- MQL5 exporter on the GPT lineage has been upgraded from heartbeat-only to a first real `EURUSD H1` FINAL-candle export using `CopyRates`, posting to `/v1/mt5/envelopes`.
- Development-only `mt5-bridge/tools/mt5_simulator.py` sends the same heartbeat and candle
  contracts as the real exporter using only Python standard-library dependencies.
- Simulator supports continuous heartbeat, `--once`, all 15 canonical instrument/timeframe
  combinations through `--matrix`, duplicate-batch, invalid-OHLC, and disconnect scenarios.
- Simulator accepts `--sequence-start` so repeated runs against a persistent backend ledger can
  continue the stable source instance sequence instead of producing a deliberate sequence conflict.
- Simulator payload generation is covered by unit tests for heartbeat and valid H1 contracts, ULID shape, reusable duplicate batch IDs, and invalid-OHLC rejection with a valid checksum.
- Durable spool recovery, exact-duplicate detection, batch/sequence conflict detection, corrupt-entry quarantine, and permanent backend rejection quarantine are implemented.
- The Python backend publisher is wired into the bridge runtime through opt-in environment
  configuration. It sends the machine API key, removes spool items only after a 2xx ACK,
  retries transient failures, and quarantines permanent backend rejection.
- ASP.NET Core exposes authenticated `POST /api/v1/bridge/candle-batches` ingestion using a
  dedicated API-key scheme. Accepted envelopes persist their candles and idempotency ledger
  in one PostgreSQL transaction. Identical retries return `duplicate`; conflicting batch or
  source-sequence reuse returns HTTP 409.
- The .NET ingestion boundary independently recomputes the canonical SHA-256 record checksum,
  enforces UTC timestamps and broker-alias consistency, and rejects mismatches before calling
  persistence.
- EF Core migration `AddMarketDataBatches` and matching directly executable DBeaver schema
  updates add the `market_data_batches` idempotency ledger.
- `scripts/setup-development.ps1` provides a portable interactive setup for new Windows
  development laptops. It stores database/JWT/bootstrap/bridge values in .NET User Secrets,
  generates random JWT and bridge keys, and never writes actual secrets into the repository.
- `scripts/setup-development.sh` provides the equivalent interactive setup for macOS and Linux.
- `appsettings.Development.example.json` documents the complete development configuration
  shape using placeholders only.
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

On 2026-08-28, the local PostgreSQL schema was upgraded through EF Core migration
`20260828044211_AddMarketDataBatches` and passed `database/999-verify-schema.sql`. The existing
development database had been created under the `postgres` owner rather than the documented
`forex_app` owner; ownership of the database and its three existing application tables was
corrected before applying the migration.

The complete local publishing path was then verified with temporary process-only credentials
and an isolated spool:

- simulator -> Python receiver -> authenticated .NET ingestion -> PostgreSQL stored one valid
  `EURUSD H1` batch and drained the spool to zero;
- an identical direct backend retry returned `202 duplicate` and left exactly one batch ledger
  row;
- while the .NET API was stopped, a valid batch remained pending at spool depth 1 and was absent
  from PostgreSQL;
- after the API restarted, the publisher replayed the pending batch, PostgreSQL stored it, and
  spool depth returned to zero with no quarantine entry.
- after configuring development secrets through the macOS setup, a repeated live local simulator
  run with source sequence 2 reached PostgreSQL successfully; the ledger contains sequences 1 and
  2 for `mt5-simulator-local`, terminal health was `HEALTHY`, and active spool depth returned to 0.
- PostgreSQL batch persistence now accepts identical candle overlap in a new batch, inserts only
  the missing candles from a mixed overlap/new batch, and rejects overlap whose business values
  differ. Concurrent batches containing the same new candle both store their ledgers while the
  canonical candle is stored only once.

On 2026-08-25, the simulator failure/recovery path was verified against a live local bridge using an isolated temporary spool:

- The duplicate scenario returned `202 accepted` for the first envelope and `202 duplicate` for the second; spool depth remained 1.
- The invalid-OHLC scenario returned `400 invalid_ohlc`; spool depth remained 1.
- With no new heartbeat, terminal health transitioned from `HEALTHY` to `WARNING` after 10 seconds and `STALE` after 20 seconds.
- A new valid heartbeat returned `202 accepted` and immediately restored terminal health to `HEALTHY`; spool depth remained 1.

The temporary bridge process was stopped and its isolated test spool was removed after verification.

## Latest automated verification

On 2026-08-28:

- `PYTHONPATH=src python -m unittest discover -s tests -v` completed successfully with 76
  tests, including machine API-key delivery and validation.
- `dotnet build ForexIntelligence.sln --no-restore --disable-build-servers -m:1` completed
  successfully with no warnings.
- `dotnet test ForexIntelligence.sln --no-build --no-restore --disable-build-servers -m:1`
  completed successfully with 27 tests passing, including PostgreSQL-backed overlap and
  concurrent batch persistence coverage.

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

- Apply migration `20260828044211_AddMarketDataBatches` to the target PostgreSQL database.
- Run a real end-to-end MT5 -> Python spool -> .NET -> PostgreSQL verification on the target machines.
- Verify concurrent duplicate delivery and backend outage/recovery against real PostgreSQL.
