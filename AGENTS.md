# Repository Guidelines

## Project Structure & Module Organization

This repository is a modular monolith. `src/ForexIntelligence.Api` owns controllers and HTTP configuration; `Application` contains familiar service interfaces, services, DTOs, and repository ports; `Domain` contains business entities, value objects, enums, and invariants without EF Core or HTTP dependencies; `Infrastructure` implements persistence and external adapters; `Worker` hosts background processing. Tests mirror those boundaries under `tests/`. The Linux-only runtime adapters are in `mt5-bridge/` and `mt5-exporter/`. Product decisions and canonical contracts live under `Development-Phases/`; update them when behavior or schemas change.

Dependencies point inward: API and Worker use Application/Infrastructure, Infrastructure implements Application ports, Application uses Domain, and Domain references no other project. Keep controllers thin. Prefer a specific repository such as `ICandleRepository` over `IRepository<T>`.

## Build, Test, and Development Commands

- `dotnet restore ForexIntelligence.sln` — restore pinned project dependencies.
- `dotnet build ForexIntelligence.sln --no-restore` — compile with warnings treated as errors.
- `dotnet test ForexIntelligence.sln --no-build --no-restore` — run all .NET tests.
- `dotnet test tests/ForexIntelligence.Domain.Tests --filter FullyQualifiedName~CandleTests` — run one test class.
- `dotnet format ForexIntelligence.sln --verify-no-changes --no-restore` — verify formatting.
- `dotnet run --project src/ForexIntelligence.Api` — start the development API.
- `dotnet tool restore` — restore the repository-local EF Core CLI.
- `psql -h localhost -U forex_app -d forex_intelligence -f database/001-initial-schema.sql` — apply the versioned schema to native PostgreSQL.
- `PYTHONPATH=mt5-bridge/src python3 -m unittest discover -s mt5-bridge/tests` — run bridge tests.

## Coding Style & Naming Conventions

`.editorconfig` enforces UTF-8, LF, four-space C# indentation, file-scoped namespaces, and sorted `System` usings. `Directory.Build.props` enables nullable references, current recommended analyzers, and warnings-as-errors. Use PascalCase for public C# members and async method names ending in `Async`. Sentence-style xUnit test names may use underscores.

## Testing Guidelines

xUnit covers Domain, Application, and API integration behavior. Domain rules must be tested without database or network access. Integration tests use `WebApplicationFactory`. Python starter tests use the standard-library `unittest` runner. Never require a live broker for the default test suite.

## Commit & Pull Request Guidelines

History uses short imperative summaries; keep commits scoped to one coherent change. PRs should state affected phase/contracts and include the exact build/test commands executed. Never commit broker credentials, account identifiers, API keys, `.env` files, Wine profiles, or bridge spool data.
