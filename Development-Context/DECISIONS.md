# Development Decisions

## 2026-08-25 — AI branch responsibilities

- `GPT`: ChatGPT conversation development workspace.
- `Codex`: Codex IDE development workspace.
- `main`: stable/shared checkpoint.
- `from-phone` and `from-pc`: legacy names; no new work should target them.
- Agents compare both active AI branches before implementing work and use this folder as a concise handoff mechanism.

## 2026-08-25 — Current implementation boundary

Stay focused on MT5/MQL5 and Python market-data acquisition before .NET ingestion. Prove the acquisition boundary with deterministic local simulation and then with a real MT5 demo terminal.

## 2026-08-29 — .NET SDK feature band

- Pin the repository to .NET SDK `10.0.400` with `rollForward: latestPatch`.
- Development and server machines may use newer `10.0.4xx` patches, but do not automatically
  cross into a later SDK feature band without an explicit repository update.

## 2026-08-25 — Simulator contract rule

The MT5 simulator must not invent a separate dummy schema. It must emit the same heartbeat and candle envelope contracts expected from the real MQL5 exporter so replacing simulator input with real MT5 input does not require changes to the Python bridge.

## 2026-08-29 — Persistent exporter sequence

- Persist the MQL5 envelope sequence per `SourceInstanceId` in MT5 Terminal Global Variables.
- Reserve the next sequence before network delivery. Sequence gaps are acceptable, but sequence
  reuse after an EA or terminal restart is not because the backend ledger treats it as conflict.

## 2026-08-29 — ACK-gated candle checkpoints

- Persist the last bridge-accepted broker open time and observed UTC offset independently for
  every canonical instrument/timeframe series.
- Backfill forward from the exact broker-history checkpoint in chronological batches capped by
  the 100-record envelope contract, advancing only after bridge HTTP 202.
- If the current broker UTC offset differs from the stored offset, pause that series. Do not guess
  historical DST conversion or silently skip the uncertain interval.

## 2026-08-30 — Market-data status is not service readiness

- Report candle freshness and gaps through an authenticated market-data status endpoint.
- Do not make `/health/ready` unhealthy solely because the forex market is closed or a series has
  no new candle; infrastructure readiness and decision-data freshness are separate concerns.
- Use a deterministic weekly UTC session window initially and calibrate it to the selected broker
  before relying on it for production decisions.

## 2026-09-05 — Target server operating system

- The dedicated target server runs antiX Linux, not Lubuntu.
- Do not assume `systemd` or use the Lubuntu `systemd` installer on the target.
- Detect and document the active antiX init system before implementing managed startup; support
  that init system while preserving non-root execution and external root-readable secret files.
- New exporter deployments use `antix-mt5-primary` as the source instance so bridge logs and new
  ledger rows identify the actual target OS. Existing `lubuntu-mt5-primary` ledger rows remain
  immutable historical records and must not be rewritten.

## Existing architecture principles

- Trading execution remains manual; the system is decision support, not an auto-trading bot.
- Deterministic calculations, validation, scoring, and risk rules must not depend on an LLM.
- AI is introduced later for classification/explanation and must consume validated data rather than raw untrusted market input.
