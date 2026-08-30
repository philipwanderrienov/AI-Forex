using ForexIntelligence.Domain.Enums;

namespace ForexIntelligence.Application.Models.MarketData;

public sealed record CandleObservation(
    string Instrument,
    Timeframe Timeframe,
    DateTimeOffset OpenTime,
    DateTimeOffset CloseTime);
