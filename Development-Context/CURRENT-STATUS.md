# Current Development Status

Last updated: 2026-09-12
Owning branch for this update: `Codex`
Next development workspace: `Codex` (user-requested IDE handoff on 2026-09-12)

## Current focus

Phase 02 operational hardening. The real MT5 -> bridge -> authenticated .NET API -> PostgreSQL
pipeline and target published API release migration, restart, reboot, and manual rollback are verified.
Next focus: validate exporter 0.6 on target and prepare candle recovery; broker-session calibration remains open.

The dedicated target server is antiX Linux, not Lubuntu. The existing `systemd` deployment
tooling must not be installed there. Native runit startup and reboot recovery have been verified.

## 2026-09-12 target compile and validated inventory

- Target MetaEditor generated exporter 0.6 code with 0 errors and 1 warning: version
  `0.6` is incompatible with the MQL5 Market version format. Target recompile of
  `0.600` also produced 0 errors and the same warning. Corrected metadata to `1.060`
  (nonzero major; logical project release remains 0.6); target recompile pending.
  No runtime logic changed. Reference: https://www.mql5.com/en/forum/13529
- User-provided inventory validates all 851 envelopes with no errors. XAUUSD H1:
  33 records = 16 legacy HTTP 401 + 1 legacy HTTP 409 + 16 antiX HTTP 409.
  AntiX candidates span September 11 05:00–20:00 WIB. Contract/checksum success
  does not prove historical timestamp correctness or authorize replay.
- Native file locking, startup, restart and recovery remain unverified. Next:
  recompile metadata fix, review current sequence floor and offset, then controlled activation.
- Local verification for metadata-only change: git diff --check passed.

## 2026-09-12 sequence conflict investigation and exporter 0.6 preparation

- User evidence: antiX source ledger sequence 1 was stored September 5 14:23:17.705 WIB;
  sequence 358 September 11 06:30:39.931; EA initialized with nextSequence=1 at 06:37:17.777;
  sequence 359 stored at 22:00:01.622. Sample 118 has different batch/checksum in quarantine.
  Quarantine 851 = 478 preserved/replayed HTTP 401 + 15 legacy HTTP 409 + 358 antiX HTTP 409
  (sequences 1–358). Exact cause of source state rollback/loss remains unproven.
- Startup sent before terminal synchronization completed. EURUSD M15/H1 then paused with
  checkpoint offset 0 versus current +10800. Current terminal sequence and ledger maximum 477.
  Only one current portable terminal and one discovered gvariables.dat; no proof of past duplicates.
- XAUUSD H1 SQL: 46 candles, 85 API gap slots, 80 open-missing slots under the +3 hypothesis.
  MT5 adjacent September 9 22:00 / September 10 01:00 broker bars match one DB gap; this
  challenges the 00:00 session hypothesis, not proof of a corrected universal session rule.
  September 10 08:00 broker candle exists in MT5 but was not found in quarantine by UTC/OHLC.
  Quarantine contains 16 distinct H1 times September 10 22:00–September 11 13:00 UTC in the
  larger gap. They remain recovery candidates, not approved replay payloads.
- Backups reported: 468 KB Custom DB archive, TOC including candle/ledger TABLE DATA readable;
  192 KB quarantine archive passes gzip check; 4.9 KB Global Variables copy. No restore test.
- Implemented locally on GPT: exporter 0.6 exclusive sequence guard plus audited bootstrap floor;
  configured/observed broker offset, recent advancing quote and 30s observation before candles;
  synchronized per-series history; bridge acceptance log explicitly distinguishes backend commit.
  Missing/corrupt/mismatched state fails closed. Existing offset-0 checkpoints stay blocked.
- Added contract-validated read-only quarantine inventory and DBeaver ledger inspection SQL.
  Rollout and recovery boundaries are in mt5-exporter/RECOVERY.md. No target changes/replay.
- Verification: bridge suite 83 tests passed with PYTHONPATH=mt5-bridge:mt5-bridge/src; the
  shorter documented PYTHONPATH failed two pre-existing tools imports from repository root.
  Subsequent modified guard scenarios passed; tools suite 7 tests passed. Guard tests execute
  production function bodies via C++ simulated MQL adapters, not actual MetaEditor/Wine APIs.
  Initial native compile is recorded above; actual file locking/durability, target startup
  and recovery remain unverified.
- Next: compile 0.6 on target while detached, obtain validated inventory, review current sequence
  floor and broker offset before activation. Guard is local to a data directory, not backend
  allocation/cross-machine fencing; restoring both state files to an old snapshot requires audit.
  Historical normalization, zero-offset checkpoint recovery, broker-history extraction and
  validated replay tooling remain outstanding. Do not copy HTTP 409 files back into spool.

## 2026-09-10 broker-session investigation and WIB decision

- Added `database/010-diagnose-xauusd-h1-gaps.sql`: read-only DBeaver diagnosis with WIB
  interval/coverage output, current API gap counts, and an explicitly hypothetical XAUUSD
  Monday-Friday 00:00-23:00 broker schedule at fixed UTC+3. See `database/README.md` for usage
  and limits. Target query results and broker-history comparison remain pending; no runtime
  schedule, timestamps, checkpoint, or quarantine changes were made.
- Verification: executed the SQL on an isolated temporary PostgreSQL 18 cluster using synthetic
  fixtures; nine checks passed (empty, single, continuous, daily break with WIB conversion,
  open-session missing candle, weekend, irregular alignment, mixed break/missing, wrong database).
  `git diff --check` passed. This is SQL verification, not target-data or broker-session validation.

- User selected WIB (`Asia/Jakarta`, UTC+7) for displays, reports, guidance, and diagnostic query
  output. Database/API timestamps remain UTC. This is a recorded presentation decision, not an
  implemented runtime or OS timezone change.
- MT5 Specification screenshots show Quotes and Trade sessions Monday-Friday 00:00-24:00 for
  EURUSD and 00:00-23:00 for XAUUSD; Saturday/Sunday are blank for both.
- Target UTC clock showed 2026-09-10 00:08:49 (07:08:49 WIB); a subsequent Market Watch screenshot
  showed about 03:09:38. These non-simultaneous observations are consistent with current broker
  UTC+3, not proof of historical offsets or DST rules.
- Assuming UTC+3, EURUSD weekly hours correspond to Monday 04:00 through Saturday 04:00 WIB;
  XAUUSD daily sessions run 04:00-03:00 the following day WIB, with a 03:00-04:00 break between
  weekday sessions. Validate these inferred conversions against actual candle history.
- Code inspection found one fixed Sunday 22:00-Friday 22:00 UTC schedule for all instruments,
  without the XAUUSD daily break. It may explain some reported gaps; full causation is unverified.
- Next: run read-only XAUUSD H1 inter-candle gap analysis in DBeaver, display timestamps using
  `AT TIME ZONE 'Asia/Jakarta'`, and compare with broker history/sessions. The previously supplied
  UTC-output query has no reported execution result. Task 21 and historical DST work remain open.

## 2026-09-10 target release verification

- Operator screenshots confirm six isolated release tests passed on antiX and Linux publish succeeded.
  First release `20260909T105658Z-27f7ce3` activated with readiness after 5 seconds.
- API-only restart recovered with API/terminal healthy, spool 0, quarantine 493; PostgreSQL and
  bridge stayed running. Exact restart readiness duration was not measured (16s was process age).
- Reboot retained the first published release and all three runit services started automatically.
  API readiness was Healthy at inspection around four minutes after boot; exact boot-to-ready
  duration was not measured. After MT5/EA started, terminal was HEALTHY and the 15-series verifier
  passed, spool was 0, and quarantine remained 493. Exporter resumed sequences 208 through 212.
- Second release `20260909T234707Z-27f7ce3` was activated and verified, then manual rollback restored
  the first release with readiness after 3 seconds. Subsequent verifier PASS, terminal HEALTHY,
  all three services running, spool 0, and quarantine 493 were confirmed.
- Final active path: `/opt/forex-intelligence/api/releases/20260909T105658Z-27f7ce3`.
  Both artifacts use the same source revision: rollback validates release switching and health,
  not compatibility between different application versions. No nonzero deployment backlog was
  captured, so these checks confirm empty spool/no new quarantine rather than measured drain time.
- Data continued advancing (M15 last close 2026-09-09T23:45:00Z). Reported gaps remain unresolved:
  EURCHF H4 12, EURGBP H1 48, XAUUSD H1 56 and M15 54; other visible FX H1/H4 counts 1 and M15 4.
  Do not equate verifier PASS with gap-free data. EURCHF/XAUUSD M15 briefly reported missing broker
  history checkpoints at MT5 startup, then successfully published again.
- Next: read-only comparison of gap intervals with broker history/session hours before changes or
  replay. Keep quarantine and its backup preserved. Optional remaining timing measurement is exact
  restart/boot readiness; the activation and rollback checks already demonstrate fast DLL startup.

## 2026-09-08 API release tooling (implementation history)

- `scripts/publish-api-release.sh` builds a versioned framework-dependent Release artifact before
  service interruption. `scripts/activate-api-release.sh` copies it into root-owned storage,
  serializes deployments, stops the old process, atomically switches `current`, and checks readiness.
- Failed activation restores and checks the previous release; `--rollback` supports manual recovery.
  The runit API template now runs the published DLL. First migration needs a source-launcher backup
  because there is no previous published release. No database migrations or secret changes occur.
- Local verification: Release publish succeeded; Bash syntax checks passed; six isolated activation
  scenarios passed (success, unhealthy candidate, startup failure, first-release failure, stop failure,
  and unhealthy rollback). Git Bash required `MSYS=winsymlinks:sys` for test symlinks on Windows.
- Target follow-up is recorded above. The Windows publish was a build check; deployment used
  artifacts published on antiX.

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
the batch/sequence conflicts before taking any action on those 15 entries. The earlier terminal-
environment startup was superseded on 2026-09-05 by managed antiX runit services with root-only
environment files.

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

During target activation, the API and bridge both ran successfully under runit and the bridge
accepted the new `antix-mt5-primary` heartbeat and candle batches with an empty active spool. A
logging defect was then found: Python structured logs use stderr, while the initial runit template
only piped stdout to `svlogd`. Both run templates now merge stderr into stdout before starting the
application.

The first reboot showed that antiX runit does not execute PostgreSQL's existing SysV runlevel
links: PostgreSQL 17 `main` remained down, API readiness correctly returned 503, and the bridge
correctly waited instead of opening its receiver. Starting PostgreSQL manually restored API and
bridge automatically. The runit deployment now also supervises the single PostgreSQL cluster on
port 5432 in foreground mode.

The first target PostgreSQL runit attempt exposed an antiX privilege detail: launching
`pg_ctlcluster` beneath `chpst -u postgres` discarded the `ssl-cert` supplementary group, so the
cluster could not read its configured snake-oil TLS private key. The service now starts the
package-provided `pg_ctlcluster` wrapper as root; that supported wrapper performs PostgreSQL's own
privilege transition while retaining the required cluster startup behavior.

The target then exposed a stop-control detail: a plain `sv restart` sent SIGTERM to the foreground
`pg_ctlcluster` wrapper and timed out while the database remained online. The runit definition now
installs `control/d` and `control/t` handlers that request a package-managed fast cluster shutdown
through `pg_ctlcluster stop` before runit restarts or leaves the service down.

The corrected target transition and second reboot then passed. Runit automatically started
PostgreSQL 17 `main`, the .NET API, both `svlogd` pipelines, and the Python bridge. PostgreSQL
accepted localhost connections, `/health/ready` returned `Healthy`, and the bridge initially
reported terminal `UNKNOWN` as expected before MT5 started. After MT5 and the updated EA started,
terminal status returned to `HEALTHY` with source instance `antix-mt5-primary`; active spool depth
was 0 and preserved quarantine depth remained 493. No manual service start was required after the
successful reboot.

The PostgreSQL control-handler follow-up also passed on the target. `sv down` completed a clean
cluster shutdown, the corrected runit service started PostgreSQL with localhost connections
available, and the final PostgreSQL/API/bridge recovery showed all three services continuously
`run`. API and terminal health returned to `Healthy`, active spool depth remained zero, quarantine
depth remained 493, and PostgreSQL no longer reported the stale `got TERM` state.

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

1. Published release target rollout, restart/reboot, and manual rollback are verified. Preserve
   the two releases and investigate the reported gap intervals against broker history next.
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
  dashboard `WAIT` behavior, an operations and credential-rotation runbook, and the minimum
  five-trading-day target soak test. The read-only exporter policy test is complete.
- Historical DST normalization is the largest current correctness risk. Applying the present
  broker offset to older bars can shift canonical UTC timestamps by one hour across a broker DST
  transition. The design must define historical offset resolution, ambiguous/nonexistent local
  times, checkpoint compatibility, and failure behavior before implementation.
- The status service currently uses a deterministic fixed UTC weekly session as an initial model.
  Its freshness and gap output is useful for target verification, but the session boundary must be
  broker-calibrated before it becomes a production decision-data gate.
- The immediate next checkpoint is gap investigation and broker-session calibration, not Phase
  03 technical-indicator development.


## September 12: exporter configuration attachment fix

Metadata build 1.061 keeps an EA with invalid configuration attached but paused,
so chart F7 / Inputs remains accessible after an initialization attempt. No timer,
heartbeat or candle publishing starts until configuration and sequence initialization
pass. Sequence-state errors still fail initialization; no guard is bypassed.

Verified: 84 bridge tests, including executing production lifecycle callbacks with
side-effect counters for invalid input, sequence refusal, timer failure and successful
activation. Native MetaEditor compilation of 1.061 and the F7 workflow remain pending.
The operator compiled 1.060 successfully, but activation still returned invalid-input
errors. Earlier target inspection found an old 0.5 source in the active MT5 directory
and a lubuntu heartbeat; quarantine rose from 851 to 864. Preserve both versions and
audit current state before recovery. Next: copy/compile 1.061 in the actual terminal
directory, attach paused, inspect Inputs and verify source/floor/offset before activation.
