using ForexIntelligence.Domain.Enums;

namespace ForexIntelligence.Application.Models;

public sealed record StoreCandleRequest(
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
