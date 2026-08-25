# Development Decisions

## 2026-08-25 — AI branch responsibilities

- `GPT`: ChatGPT conversation development workspace.
- `Codex`: Codex IDE development workspace.
- `main`: stable/shared checkpoint.
- `from-phone` and `from-pc`: legacy names; no new work should target them.
- Agents compare both active AI branches before implementing work and use this folder as a concise handoff mechanism.

## 2026-08-25 — Current implementation boundary

Stay focused on MT5/MQL5 and Python market-data acquisition before .NET ingestion. Prove the acquisition boundary with deterministic local simulation and then with a real MT5 demo terminal.

## 2026-08-25 — Simulator contract rule

The MT5 simulator must not invent a separate dummy schema. It must emit the same heartbeat and candle envelope contracts expected from the real MQL5 exporter so replacing simulator input with real MT5 input does not require changes to the Python bridge.

## Existing architecture principles

- Trading execution remains manual; the system is decision support, not an auto-trading bot.
- Deterministic calculations, validation, scoring, and risk rules must not depend on an LLM.
- AI is introduced later for classification/explanation and must consume validated data rather than raw untrusted market input.
