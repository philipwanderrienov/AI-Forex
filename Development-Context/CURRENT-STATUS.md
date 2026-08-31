# Current Development Status

Last updated: 2026-08-31
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
- MQL5 exporter reads all 15 canonical instrument/timeframe combinations using `CopyRates`
  and posts FINAL candles to `/v1/mt5/envelopes`.
- Exporter sequence state is persisted per `SourceInstanceId` in MT5 Terminal Global Variables
  before delivery, preventing sequence reuse after EA or terminal restart.
- Exporter version 0.5 also persists a candle checkpoint for each of the 15 canonical series.
  It replays missing closed bars chronologically in batches capped at 100 records, advances a
  checkpoint only after bridge HTTP 202, and pauses rather than guessing across broker UTC-offset
  changes.
- Authenticated `GET /api/market-data/status` reports deterministic freshness and recent gap
  counts for every canonical instrument/timeframe series. It distinguishes `FRESH`, `STALE`,
  `GAP_DETECTED`, `MARKET_CLOSED`, and `UNKNOWN` without making service readiness fail merely
  because the weekly market session is closed.
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
- Database bootstrap, schema, and verification scripts now fail fast when a DBeaver editor is
  connected to the wrong database. Schema and verification scripts may use an administrator
  connection but execute under transaction-local role `forex_app`, preserving least-privilege
  object ownership without requiring a second DBeaver connection. Verification also checks
  database/table ownership and all primary-key and secondary indexes.
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

On 2026-08-29, the dedicated Linux server laptop completed the local backend handoff using
PostgreSQL 17.11, .NET SDK 10.0.400, ASP.NET Core, and the Python bridge on the same machine.
The target schema and batch-ledger migration were applied under `forex_app`, `/health/ready`
reported `Healthy`, and the bridge authenticated using the locally stored machine API key. A
simulator candle remained at spool depth 1 while the backend/schema was unavailable, then replayed
successfully after recovery: EF Core inserted both `candles` and `market_data_batches`, DBeaver
showed the `mt5-simulator-local` sequence-1 ledger row, and no quarantine entry was created.

The real exporter version 0.3 then completed the full server path. Heartbeats from
`lubuntu-mt5-primary` were accepted, and PostgreSQL stored FINAL candles for all five canonical
instruments across M15, H1, and H4. DBeaver showed 16 candle rows: 15 real MT5 combinations plus
the earlier simulator candle. This verifies MT5 -> Python bridge -> authenticated .NET ingestion
-> PostgreSQL for the planned acquisition matrix.

Exporter version 0.4 was subsequently compiled, attached, and restarted on the target terminal.
The `lubuntu-mt5-primary` ledger retained monotonic sequence state: DBeaver reported sequence 3
through 212 across 30 stored batches. Gaps reflect sequences reserved before failed deliveries and
are valid; the sequence did not reset, the bridge spool drained to zero, and quarantine remained
zero. Re-published overlapping candles remained duplicate-safe in canonical candle storage.

On 2026-08-31, exporter version 0.5 completed its short target-terminal outage checkpoint test.
The EA was detached for approximately 20 minutes and then attached again. Before the outage, the
latest displayed M15 checkpoints were `2026-08-31T05:00:00Z` through sequence 113. On startup the
exporter recovered `nextSequence=114`, published the next closed M15 candle for all five canonical
instruments with checkpoint `2026-08-31T05:15:00Z`, and used sequences 114 through 118. The bridge
continued accepting heartbeats and the backend persisted the resumed batches. This verifies
checkpoint catch-up for a short outage that did not cross a broker UTC-offset transition.

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

On 2026-08-30:

- The repository SDK pin was upgraded from `10.0.201` to `10.0.400` with
  `rollForward: latestPatch` to match the server development environment.
- `dotnet restore ForexIntelligence.sln` completed successfully using SDK `10.0.400`.
- `PYTHONPATH=src python -m unittest discover -s tests -v` completed successfully with 82
  tests, including machine API-key delivery and validation.
- `dotnet build ForexIntelligence.sln --no-restore --disable-build-servers -m:1` completed
  successfully with no warnings in a compatibility run using local SDK 10.0.201 after a matching
  restore; the repository remains pinned to SDK 10.0.400.
- `dotnet test ForexIntelligence.sln --no-build --no-restore --disable-build-servers -m:1`
  completed successfully with 37 tests passing: 10 Domain, 10 Application, and 17 Integration.
  The target server still needs to repeat this checkpoint with the pinned SDK 10.0.400.

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

- Run the new .NET market-data status tests with SDK 10.0.400 and verify the authenticated status
  response against target PostgreSQL.
- Implement broker-aware historical DST normalization before allowing automatic backfill across
  a detected UTC-offset transition.
- Upgrade the target server from PostgreSQL 17.11 to the repository target PostgreSQL 18.x before
  production deployment.
