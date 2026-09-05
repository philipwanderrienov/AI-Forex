# Current Development Status

Last updated: 2026-09-05
Owning branch for this update: `Codex`

## Current focus

Phase 02 market-data acquisition. The MT5/Python acquisition boundary is complete enough to
move development into authenticated .NET ingestion and PostgreSQL persistence.

The dedicated target server is antiX Linux, not Lubuntu. The existing `systemd` deployment
tooling must not be installed there; managed startup must first be adapted to the active antiX
init system.

The exporter default source instance is now `antix-mt5-primary`, preventing new bridge logs and
ledger rows from labeling the target as Lubuntu. Applying this identity on the existing terminal
is an explicit migration because source identity owns independent sequence and checkpoint state.

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
- `tools/verify_market_data_status.py` provides a credential-safe target verifier. It prompts for
  the bootstrap password, obtains a short-lived token, calls the authenticated status endpoint,
  and fails unless the response contains exactly the 15 canonical instrument/timeframe series
  with valid status and gap fields.
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
- Native antiX runit definitions and an installer are available for managed API/bridge startup.
  Secrets remain in root-readable `/etc/forex-intelligence/*.env` files, the installer does not
  activate services, both applications run as the non-root repository owner, bridge startup waits
  for API readiness, and `svlogd` owns bounded service logs. Legacy `systemd` templates remain for
  other Linux targets but are not used on the antiX server.
- The exporter source policy test rejects direct order APIs, `CTrade` order/position methods,
  `MqlTradeRequest`, and trading action constants so the acquisition boundary remains read-only.
- `tools/audit_bridge_quarantine.py` provides a read-only summary of rejection categories and
  exposes only batch ID, source instance, sequence, and checksum for HTTP 409 ledger review.
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

## Target-server status verification checkpoint

On 2026-09-02, the authenticated market-data status verifier ran successfully against the target
server API at `http://127.0.0.1:5204`. The API returned exactly all 15 canonical
instrument/timeframe series and the verifier reported `PASS`. PostgreSQL readiness also returned
`Healthy` after correcting the .NET User Secrets connection string so its `forex_app` password
matched the database role. The observed series were still `GapDetected` and stale, so this proves
the endpoint contract and database connectivity but does not yet prove current decision-data
freshness or broker-session calibration.

During this verification, the bridge publisher was first started without the active backend
configuration and then with a bridge API key that did not match the .NET API. Pending envelopes
therefore accumulated and were classified as permanent backend rejections. After restarting both
processes with the .NET API using its User Secrets value and the bridge reading that same value,
new batches reached PostgreSQL successfully: the API logged inserts into both `candles` and
`market_data_batches`, and active spool depth returned to zero.

The durable quarantine remains intentionally untouched at 493 envelopes. A read-only metadata
audit found:

- 478 `permanent_backend_rejection` entries with HTTP 401 caused by the temporary API-key
  mismatch; these are candidates for controlled replay.
- 15 `permanent_backend_rejection` entries with HTTP 409; do not replay these until their
  batch/sequence conflicts are reviewed.

On 2026-09-03, the target-server recovery was completed without changing source code. The operator
stopped the Python bridge, created a backup of the quarantine, copied only the 478 HTTP 401
payloads back to the active spool, and restarted the bridge with
`MT5_BRIDGE_BACKEND_URL` targeting port 5204 and `MT5_BRIDGE_BACKEND_API_KEY` sourced from the
matching .NET User Secret. Replay drained from 478 pending envelopes to zero while the API logged
successful inserts into both `candles` and `market_data_batches`. After the EA and Algo Trading
were enabled again, terminal health returned to `HEALTHY`, heartbeat age remained near zero, the
active spool remained empty, and quarantine depth remained unchanged at 493.

The quarantine and its backup remain intentionally preserved. They contain copies of the 478
successfully replayed HTTP 401 payloads and the 15 HTTP 409 payloads that were not replayed. Review
the batch/sequence conflicts before taking any action on those 15 entries. The currently running
bridge receives its backend URL and API key from the launching terminal environment, so a terminal
close or server restart still requires the same secret-loading startup sequence. Recommended next
operational hardening: define managed startup services for the API and bridge with secure secret
loading, and add a documented controlled-quarantine audit/replay procedure.

On the same day, a controlled EA-only outage lasted approximately 52 minutes while the API and
bridge remained running. Terminal health correctly became `STALE`. After reattaching the EA,
sequence values continued in the 3700 range, missed M15 candles were published chronologically,
the authenticated 15-series verifier passed, recent gap counts did not increase, active spool
depth returned to zero, and quarantine depth remained 493. A read-only audit confirmed the 15
preserved HTTP 409 entries; a sampled entry reused source sequence 206 with a different batch ID
than the PostgreSQL ledger and is therefore a valid historical sequence conflict that must not be
replayed.

## Latest automated verification

On 2026-09-05, the antiX/runit and exporter identity update passed:

- shell syntax validation for the runit installer and all three run-script templates;
- `PYTHONPATH=src python3 -m unittest discover -s tests -v` with all 82 bridge tests passing;
- `dotnet test ForexIntelligence.sln --no-restore --disable-build-servers -m:1` with all 37
  tests passing; and
- `git diff --check` with no whitespace errors.

Target installation and reboot verification of the runit services remains pending.

On 2026-09-03, the managed-startup/quarantine-audit change passed:

- `python -m unittest tools/test_audit_bridge_quarantine.py tools/test_verify_market_data_status.py -v`
  with all 4 tests passing;
- `PYTHONPATH=src python -m unittest discover -s tests -v` from `mt5-bridge/` with all
  82 bridge tests passing; and
- `bash -n scripts/install-server-services.sh` using Git Bash.

Target installation and reboot verification of the systemd units remains intentionally pending;
the installer does not activate services while environment files still contain placeholders.

On 2026-09-01, the Windows Codex workspace repeated the .NET checkpoint with the repository-pinned
SDK `10.0.400`:

- `dotnet restore ForexIntelligence.sln` completed successfully after refreshing the API package
  cache;
- `dotnet build ForexIntelligence.sln --no-restore --disable-build-servers -m:1` completed with
  zero warnings and zero errors;
- `dotnet test ForexIntelligence.sln --no-build --no-restore --disable-build-servers -m:1`
  completed with all 37 tests passing: 10 Domain, 10 Application, and 17 Integration.
- `python -m unittest tools/test_verify_market_data_status.py -v` completed with both target
  verifier contract tests passing.

The local PostgreSQL 18 service is present, but this Windows workspace has no API User Secrets
file, so authenticated status verification against PostgreSQL was not attempted with guessed or
hard-coded credentials. Target-server endpoint verification and broker-session calibration remain
open.

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

- Calibrate current `lastCloseTime`, `ageMinutes`, and `gapCount` expectations against the
  selected broker at weekly close/open boundaries. The 478 HTTP 401 quarantine payloads were
  already replayed successfully and short-outage recovery passed; broker-session boundary
  calibration remains unverified.
- Calibrate the initial Sunday 22:00 UTC through Friday 22:00 UTC market-session window in
  `ForexMarketSchedule` against the selected broker before relying on it for production decisions.
- Implement broker-aware historical DST normalization before allowing automatic backfill across
  a detected UTC-offset transition.
- Upgrade the target server from PostgreSQL 17.11 to the repository target PostgreSQL 18.x before
  production deployment.

## Recommended next development sequence

1. Detect the active antiX init system, add compatible managed API/bridge startup with secure
   secret loading, then install and reboot-verify it on the target.
2. Calibrate and test the broker's weekly UTC market-session boundaries, including market-open,
   Friday close, Sunday open, and short-outage behavior.
3. Design broker-aware historical timezone/DST normalization. The current exporter intentionally
   pauses a series when its stored checkpoint offset differs from the current broker offset; do
   not convert historical broker timestamps using only the current offset.
4. Implement the agreed normalization and verify restart/backfill across a real or deterministic
   UTC-offset transition without shifted, duplicated, or silently missing candles.
5. Audit the remaining Phase 02 acceptance criteria before moving Phase 03 into primary focus.

## Remaining Phase 02 scope and risks

- The candle acquisition foundation is proven end to end, but Phase 02 as documented is not yet
  complete. Remaining scope includes tick/spread acquisition, read-only account telemetry,
  broker-chart comparison, detailed `NO_TICK`/`SYMBOL_DISABLED`/disconnect observability,
  dashboard `WAIT` behavior, an operations and credential-rotation runbook, a policy test proving
  the exporter cannot execute orders, and the minimum five-trading-day target soak test.
- Historical DST normalization is the largest current correctness risk. Applying the present
  broker offset to older bars can shift canonical UTC timestamps by one hour across a broker DST
  transition. The design must define historical offset resolution, ambiguous/nonexistent local
  times, checkpoint compatibility, and failure behavior before implementation.
- The status service currently uses a deterministic fixed UTC weekly session as an initial model.
  Its freshness and gap output is useful for target verification, but the session boundary must be
  broker-calibrated before it becomes a production decision-data gate.
- The immediate next checkpoint is target verification and broker-session calibration, not Phase
  03 technical-indicator development.
