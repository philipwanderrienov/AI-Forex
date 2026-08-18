using ForexIntelligence.Domain.Entities;
using ForexIntelligence.Domain.Enums;
using ForexIntelligence.Domain.Exceptions;

namespace ForexIntelligence.Domain.Tests;

public sealed class CandleTests
{
    [Fact]
    public void Create_WithValidValues_ReturnsCanonicalCandle()
    {
        var candle = Candle.Create(
            "eurusd",
            Timeframe.H1,
            new DateTimeOffset(2026, 8, 18, 8, 0, 0, TimeSpan.Zero),
            new DateTimeOffset(2026, 8, 18, 9, 0, 0, TimeSpan.Zero),
            1.1700m,
            1.1750m,
            1.1680m,
            1.1730m,
            100,
            CandleStatus.Final);

        Assert.Equal("EURUSD", candle.Instrument);
        Assert.Equal(Timeframe.H1, candle.Timeframe);
        Assert.Equal(CandleStatus.Final, candle.Status);
    }

    [Fact]
    public void Create_WithInvalidOhlc_ThrowsDomainValidationException()
    {
        var action = () => Candle.Create(
            "EURUSD",
            Timeframe.H1,
            new DateTimeOffset(2026, 8, 18, 8, 0, 0, TimeSpan.Zero),
            new DateTimeOffset(2026, 8, 18, 9, 0, 0, TimeSpan.Zero),
            1.1700m,
            1.1690m,
            1.1680m,
            1.1730m,
            100,
            CandleStatus.Final);

        Assert.Throws<DomainValidationException>(action);
    }

    [Fact]
    public void Create_WithNonUtcTimestamp_ThrowsDomainValidationException()
    {
        var action = () => Candle.Create(
            "EURUSD",
            Timeframe.H1,
            new DateTimeOffset(2026, 8, 18, 15, 0, 0, TimeSpan.FromHours(7)),
            new DateTimeOffset(2026, 8, 18, 16, 0, 0, TimeSpan.FromHours(7)),
            1.1700m,
            1.1750m,
            1.1680m,
            1.1730m,
            100,
            CandleStatus.Final);

        Assert.Throws<DomainValidationException>(action);
    }
}
