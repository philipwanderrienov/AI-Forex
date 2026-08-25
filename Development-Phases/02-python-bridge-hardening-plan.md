# Phase 02 — Python Bridge Hardening Plan

## Goal

Make the Python MT5 bridge ready for real MetaTrader 5 integration before the Lubuntu collector machine is available. Until then, the MT5 simulator is the executable contract fixture.

The Python bridge owns transport reliability, contract validation, bounded local buffering, replay/retry, health, configuration, and observability. Trading decisions, technical indicators, scoring, and risk business rules remain outside Python.

## Definition of pre-MT5 complete

The bridge is ready for real MT5 integration when all simulator-driven positive/failure scenarios below are automated, restart/recovery behavior is deterministic, the spool cannot silently lose or overwrite accepted batches, duplicate/replayed input is safe, and backend outages can be simulated without a real .NET backend.

## Test matrix

### Positive cases

- [x] Valid heartbeat is accepted.
- [x] Valid candle envelope is accepted and durably spooled.
- [x] Simulator happy path is documented/verified.
- [ ] Multiple valid candle records in one envelope preserve order.
- [ ] Consecutive envelope sequences are accepted.
- [ ] Restart reloads pending spool entries in FIFO order.
- [ ] Replay removes an entry only after downstream acknowledgement.
- [ ] Health reports healthy terminal and available spool under normal load.

### Contract and data failures

- [x] Malformed/invalid heartbeat fields are rejected.
- [x] Unsupported schema versions are rejected.
- [x] Invalid batch/checksum/UTC/decimal/OHLC invariants are rejected by contract validation.
- [ ] Malformed JSON returns a deterministic client error and does not touch the spool.
- [ ] Empty records are rejected.
- [ ] Envelope record limit overflow is rejected.
- [ ] Unsupported instrument/timeframe/payload type is rejected.
- [ ] Non-positive candle prices are rejected.
- [ ] Broker alias mismatch between envelope and records is rejected.
- [ ] Invalid FINAL candle timing/finality is rejected where contract context permits.

### Reliability and operational failures

- [x] Terminal freshness transitions through UNKNOWN/HEALTHY/WARNING/STALE.
- [x] Spool item/byte capacity and disk availability are observable.
- [ ] Duplicate batch ID is idempotent and never creates a second pending item.
- [ ] Duplicate sequence with conflicting batch content is rejected/quarantined.
- [ ] Out-of-order sequence is detected and surfaced.
- [ ] Spool-full rejection never deletes an older pending entry.
- [ ] Corrupt spool entry is detected and quarantined rather than silently skipped.
- [ ] Process restart while entries are pending preserves accepted data.
- [ ] Graceful shutdown leaves spool in a recoverable state.
- [ ] Simulated backend timeout keeps the item pending.
- [ ] Simulated backend 5xx retries with exponential backoff + jitter.
- [ ] Simulated backend 4xx permanent rejection does not retry forever and is observable.
- [ ] Successful downstream acknowledgement advances replay/checkpoint exactly once.

## Implementation order

1. Extend simulator/test fixtures for multi-record, duplicate, sequence and malformed input scenarios.
2. Add durable idempotency and sequence/checkpoint state around the spool.
3. Add a backend publisher abstraction plus fake downstream server for tests; do not require .NET yet.
4. Implement bounded retry with exponential backoff + jitter and acknowledgement-driven spool removal.
5. Add corrupt-entry quarantine and deterministic restart/recovery tests.
6. Add structured logging and configuration tests with explicit secret-redaction rules.
7. Run a local soak/load simulation and record acceptance evidence.
8. Only after the above is green, connect the real MT5/Wine exporter and validate broker-specific behavior.

## Deferred until real MT5 is available

- Broker symbol suffix/prefix discovery against the actual broker.
- Real M15/H1/H4 candle comparison with broker charts.
- Real tick freshness/spread comparison.
- Broker/server timezone and DST validation.
- Terminal disconnect/reconnect behavior under Wine.
- Historical backfill availability and broker history depth.
- Account telemetry comparison with the terminal.

## Exit status

When all non-deferred checks are green, mark the Python component **Ready for Real MT5 Integration**. This does not complete all of Phase 02: .NET ingestion, PostgreSQL/Redis persistence, and end-to-end production integration remain later Phase 02 work.
