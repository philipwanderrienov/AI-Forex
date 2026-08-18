using ForexIntelligence.Domain.Enums;

namespace ForexIntelligence.Api.Models.Requests.MarketData;

public sealed record StoreCandleApiRequest(
    string Instrument,
    Timeframe Timeframe,
    DateTimeOffset OpenTime,
    DateTimeOffset CloseTime,
    decimal Open,
    decimal High,
    decimal Low,
    decimal Close,
    long TickVolume,
    CandleStatus Status);
