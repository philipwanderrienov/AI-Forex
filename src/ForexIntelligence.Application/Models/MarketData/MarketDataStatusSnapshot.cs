using ForexIntelligence.Domain.Enums;

namespace ForexIntelligence.Application.Models.MarketData;

public enum MarketDataFreshnessStatus
{
    Unknown,
    Fresh,
    Stale,
    GapDetected,
    MarketClosed
}

public sealed record MarketDataSeriesStatus(
    string Instrument,
    Timeframe Timeframe,
    MarketDataFreshnessStatus Status,
    DateTimeOffset? LastOpenTime,
    DateTimeOffset? LastCloseTime,
    double? AgeMinutes,
    int GapCount);

public sealed record MarketDataStatusSnapshot(
    MarketDataFreshnessStatus Status,
    DateTimeOffset EvaluatedAt,
    bool MarketOpen,
    IReadOnlyCollection<MarketDataSeriesStatus> Series);
