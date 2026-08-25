# Repository Guidelines

## AI Development Branch Protocol

This repository uses Git branches as the shared context bridge between ChatGPT conversation work and Codex IDE work.

- `main` is the stable/shared checkpoint. Do not use it as the default development workspace.
- `GPT` is the workspace for development performed from ChatGPT conversations.
- `Codex` is the workspace for development performed by Codex in the IDE.
- Legacy branches `from-phone` and `from-pc` are superseded by `GPT` and `Codex` respectively and must not receive new development work.

Before starting development, an AI agent must:

1. Fetch/inspect `main`, `GPT`, and `Codex`.
2. Compare its own branch with the other AI branch and `main`.
3. Read `Development-Context/CURRENT-STATUS.md`, `Development-Context/NEXT-TASKS.md`, and `Development-Context/DECISIONS.md` when present.
4. Inspect recent commits on both AI branches so completed work is not implemented twice.
5. Work only on its assigned branch unless the user explicitly requests another branch or a merge.

After a meaningful development change, the AI agent must update the relevant Development-Context document so the other agent can resume without requiring the user to restate project context. Record what changed, what was verified, important limitations, and the recommended next step. Keep these files concise and factual; source code and canonical Development-Phases documents remain authoritative for implementation details.

Do not automatically merge `GPT` and `Codex`. If one branch needs work from the other, compare the branches first and explicitly merge/cherry-pick only when requested or clearly required for the current task. Resolve conflicts deliberately rather than overwriting another agent's work.

## Project Structure & Module Organization

This repository is a modular monolith. `src/ForexIntelligence.Api` owns controllers and HTTP configuration; `Application` contains familiar service interfaces, services, DTOs, and repository ports; `Domain` contains business entities, value objects, enums, and invariants without EF Core or HTTP dependencies; `Infrastructure` implements persistence and external adapters; `Worker` hosts background processing. Tests mirror those boundaries under `tests/`. The Linux-only runtime adapters are in `mt5-bridge/` and `mt5-exporter/`. Product decisions and canonical contracts live under `Development-Phases/`; update them when behavior or schemas change.

Dependencies point inward: API and Worker use Application/Infrastructure, Infrastructure implements Application ports, Application uses Domain, and Domain references no other project. Keep controllers thin. Prefer a specific repository such as `ICandleRepository` over `IRepository<T>`.

All repository SQL scripts must be directly executable in DBeaver. Do not add terminal-specific commands, terminal-only setup paths, or a separate DBeaver-specific subfolder; keep numbered SQL scripts directly under `database/`.

## Build, Test, and Development Commands

- `dotnet restore ForexIntelligence.sln` — restore pinned project dependencies.
- `dotnet build ForexIntelligence.sln --no-restore` — compile with warnings treated as errors.
- `dotnet test ForexIntelligence.sln --no-build --no-restore` — run all .NET tests.
- `dotnet test tests/ForexIntelligence.Domain.Tests --filter FullyQualifiedName~CandleTests` — run one test class.
- `dotnet format ForexIntelligence.sln --verify-no-changes --no-restore` — verify formatting.
- `dotnet run --project src/ForexIntelligence.Api` — start the development API.
- `dotnet tool restore` — restore the repository-local EF Core CLI.
- Open the numbered scripts under `database/` in DBeaver and execute them in order — apply or verify the native PostgreSQL schema.
- `PYTHONPATH=mt5-bridge/src python3 -m unittest discover -s mt5-bridge/tests` — run bridge tests.

## Coding Style & Naming Conventions

`.editorconfig` enforces UTF-8, LF, four-space C# indentation, file-scoped namespaces, and sorted `System` usings. `Directory.Build.props` enables nullable references, current recommended analyzers, and warnings-as-errors. Use PascalCase for public C# members and async method names ending in `Async`. Sentence-style xUnit test names may use underscores.

## Testing Guidelines

xUnit covers Domain, Application, and API integration behavior. Domain rules must be tested without database or network access. Integration tests use `WebApplicationFactory`. Python starter tests use the standard-library `unittest` runner. Never require a live broker for the default test suite.

## Commit & Pull Request Guidelines

History uses short imperative summaries; keep commits scoped to one coherent change. PRs should state affected phase/contracts and include the exact build/test commands executed. Never commit broker credentials, account identifiers, API keys, `.env` files, Wine profiles, or bridge spool data.
