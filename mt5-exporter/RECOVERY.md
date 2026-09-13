# Exporter 0.6 rollout and recovery checkpoint

## Current operator checkpoint (2026-09-13, WIB)

Target metadata 1.062 initializes at nextSequence 478 and reports QUOTE_STALE
with expectedOffset 10800. Live candle acceptance and backend persistence remain
unverified until advancing quotes arrive. The 31 XAUUSD H1 candles covered by
SQL 012/013 have been recovered; four remaining hourly slots also have no bars
in the supplied CSV. EURUSD checkpoint samples matched DB; offset-only repair
was guided, but live traversal remains unverified.

The bridge now uses `/var/lib/forex-intelligence/spool`: migration verified 1702
files, retained the source, and restarted healthy with pending 0/quarantine 851.
Source and virtualenv still depend on the checkout. See
[CURRENT-STATUS.md](../Development-Context/CURRENT-STATUS.md) and
[NEXT-TASKS.md](../Development-Context/NEXT-TASKS.md) for current evidence and tasks.
The historical preparation steps below are not instructions to repeat completed
repairs or reset initialized state.

## Evidence and backups (2026-09-12, WIB)

The target ledger first stored `antix-mt5-primary` sequence 1 on September 5 at
14:23:17.705, sequence 358 on September 11 at 06:30:39.931, and sequence 359 on
September 11 at 22:00:01.622. EA logs show startup with `nextSequence=1` at
06:37:17.777 on September 11. Sample sequence 118 has different batch IDs and
checksums in the ledger and quarantine. The precise cause of local state loss or
identity reuse is unknown; renaming the source alone is not an explanation.

The terminal reported synchronization at 06:37:19.894 after the EA's first send
at 06:37:19.377. EURUSD M15/H1 then paused with checkpoint offset 0 and current
10800. This supports a startup-time readiness problem, not a proven DST change.

Target quarantine contains 851 pairs: 478 preserved HTTP 401 envelopes previously
replayed, 15 legacy-source HTTP 409 envelopes, and 358 antiX-source HTTP 409
envelopes with sequences 1–358. XAUUSD H1 has 33 records in quarantine, including
16 distinct UTC open times from September 10 22:00 through September 11 13:00.
The September 10 05:00 UTC candle seen in MT5 (08:00 broker) was not found by
UTC or OHLC matching. It requires broker-history recovery if still absent in DB.
Do not treat all quarantine records as missing or all gap slots as trading hours.

Backups reported on target:

- `~/Dokumen/forex_intelligence_before_recovery_20260912.backup.sql`: 468 KB Custom
  dump; `pg_restore --list` reads schema and TABLE DATA for candles and ledger.
  Restore has not been tested; the `.sql` suffix does not imply plain SQL.
- `~/forex-recovery-backups/quarantine-20260912-213012.tar.gz`: 192 KB; gzip check passed.
- `~/forex-recovery-backups/gvariables-20260912-213103.dat`: 4.9 KB copy.

## Configuration dialog recovery (metadata build 1.061)

Invalid configuration now leaves the EA attached and paused with a chart message.
Open chart F7 -> Inputs to correct the configuration. While paused it creates no
timer and sends neither heartbeat nor candles; bridge terminal freshness can be stale.
Sequence initialization failures still stop the EA and require an audit.

Close MetaEditor before replacing the active source to avoid saving an older open
buffer over it. Compile the source in the actual terminal MQL5/Experts directory.
The target subsequently demonstrated the configuration dialog and successful
initialization; the latest runtime screenshot is from metadata build 1.062.
The later operator snapshot reported quarantine depth 864 and a lubuntu heartbeat
after an old 0.5 exporter ran; the 851-pair backup above predates that event.

## What 0.6 changes

- A missing `.guard` file requires an explicitly audited `VerifiedSequenceFloor`.
  All series checkpoints must be present when the starting sequence is positive
  (including a restart after an interrupted first initialization). The floor
  is the maximum reserved/accepted sequence across ledger, pending spool,
  quarantine and terminal state, not just the latest stored batch.
- Each reservation writes and flushes a sequence/check pair to the guard before
  updating the Global Variable and before sending. A missing variable, mismatch,
  truncated/corrupt guard or write failure stops publishing. No automatic reset.
- The guard stays exclusively open, preventing another 0.6 exporter for this
  source in the same data directory. This does not lock another computer/profile
  or an old 0.5 EA. Only one producer may use a source identity.
- Candle publishing requires an explicitly verified current broker offset,
  connection, a recent quote, matching observed offset, 30 seconds of observation
  and a quote that advances. Each series must load synchronized history. No
  quotes at weekend/startup means candle publishing waits; heartbeat may continue.
- Checkpoint offset mismatches remain blocked. Configuring +10800 does not repair
  existing zero-offset checkpoints or authorize historical conversions.
- The acceptance log now says bridge acceptance with backend persistence pending.
  Checkpoints still advance on durable bridge HTTP 202; 0.6 does not implement a
  backend commit acknowledgement. Backend rejection still needs recovery review.

## Prepare and compile on target

1. Keep MT5 stopped while reviewing state. Preserve the backups above.
2. Copy `ForexIntelligenceDataExporter.mq5` into the existing terminal's
   `MQL5/Experts` directory. Keep a copy of the prior `.mq5` and `.ex5` outside
   that active directory. No API/bridge release or database migration is needed.
3. Compile with MetaEditor and require zero errors. Local C++ adapter tests do
   not substitute for this native compile or MT5/Wine file-lock verification.
4. With the EA detached, use `database/011-inspect-recovery-ledger.sql` in DBeaver
   and the read-only audits below. Confirm no second source producer and no pending
   spool. Check the terminal sequence too. The last observed target maximum was
   477; recheck it rather than treating 477 as a permanent configuration value.
5. For first 0.6 activation, set `VerifiedSequenceFloor` to the reviewed maximum,
   retain `SourceInstanceId=antix-mt5-primary`, and set
   `ExpectedBrokerUtcOffsetSeconds=10800` only if the current broker offset is
   still verified as +3. Defaults intentionally refuse unreviewed activation.
6. Attach on one chart only. Check initialization, guard creation and paused
   reasons. EURUSD M15/H1 with stored offset 0 will remain paused. Offset edits
   require exact broker-history/DB evidence; do not blindly change them to +3.
   Outside trading hours the clock gate intentionally waits for quotes.
7. After successful first initialization, return `VerifiedSequenceFloor` to -1;
   the existing guard supports subsequent starts. Back up BOTH `Bases/gvariables.dat`
   and `MQL5/Files/ForexIntelligence.Sequence.*.guard` with MT5 stopped.
8. At market open verify readiness, sequence continuity, unchanged quarantine,
   API/bridge health and all 15 series. An activation test is not recovery completion.

Both local state files restored together to an old snapshot can evade the local
comparison. Any restore, source migration or profile change requires a fresh
ledger/spool/quarantine audit. This release does not provide backend sequence
allocation or cross-machine fencing. Returning to 0.5 after 0.6 reservations can
make the guard stale and must also be audited; do not simply delete it.

## Read-only recovery inventory

From the repository root on antiX:

```bash
python3 tools/inspect_quarantine_candles.py > "$HOME/forex-recovery-backups/xauusd-h1-inventory.json"
```

The report validates complete envelopes/checksums, includes original IDs,
sequence, UTC/WIB open time, OHLC, tick volume and rejection category, and reports
unreadable or missing file pairs. Nonzero exit or `errors` means the inventory is
incomplete. It never writes to quarantine or sends requests. `--instrument` and
`--timeframe` select other canonical series. Keep reports outside Git.

Before any recovery write, compare candidate business values and timestamps with
broker history and canonical DB rows, detect conflicting overlaps, resolve the
zero-offset checkpoints, and establish historical offsets for the exact period.
Preserve original envelope provenance. Do not copy HTTP 409 envelopes into spool,
rename their source, or alter checksums/sequence ad hoc. The report is preparation,
not an executable replay plan. The scoped CSV repairs recorded above are complete;
any additional recovery requires its own evidence. Quarantine replay is not authorized
by a successful inventory or by those manual candle repairs.

## Verification commands

```bash
PYTHONPATH=mt5-bridge:mt5-bridge/src python3 -m unittest discover -s mt5-bridge/tests
python3 -m unittest discover -s tools -p 'test_*.py'
git diff --check
```

`test_exporter_guards.py` compiles the actual guard function bodies in a C++ harness
with simulated platform adapters. It covers state loss, rollback, corrupt guard,
exclusive-open failure, sequence exhaustion/invalid values, disk write failure,
clock startup, fresh quotes and reconnect. It does not execute actual MQL file APIs.

MQL API references: [FileOpen](https://www.mql5.com/en/docs/files/fileopen),
[TimeTradeServer](https://www.mql5.com/en/docs/dateandtime/timetradeserver).
