using ForexIntelligence.Application.Interfaces.Repositories;
using ForexIntelligence.Application.Models.MarketData;
using ForexIntelligence.Application.Services;
using ForexIntelligence.Domain.Enums;

namespace ForexIntelligence.Application.Tests;

public sealed class MarketDataStatusServiceTests
{
    [Fact]
    public async Task GetStatusAsync_WithoutCandles_ReturnsUnknownForAllSeries()
    {
        var service = CreateService(new DateTimeOffset(2026, 8, 31, 10, 5, 0, TimeSpan.Zero));

        var result = await service.GetStatusAsync(CancellationToken.None);

        Assert.Equal(MarketDataFreshnessStatus.Unknown, result.Status);
        Assert.True(result.MarketOpen);
        Assert.Equal(15, result.Series.Count);
        Assert.All(result.Series, series => Assert.Equal(MarketDataFreshnessStatus.Unknown, series.Status));
    }

    [Fact]
    public async Task GetStatusAsync_WithRecentFinalCandle_ReturnsFreshSeries()
    {
        var now = new DateTimeOffset(2026, 8, 31, 10, 5, 0, TimeSpan.Zero);
        var observations = new[]
        {
            Candle("EURUSD", Timeframe.M15, 9, 45)
        };
        var service = CreateService(now, observations);

        var result = await service.GetStatusAsync(CancellationToken.None);

        var eurUsd = Assert.Single(result.Series, series =>
            series.Instrument == "EURUSD" && series.Timeframe == Timeframe.M15);
        Assert.Equal(MarketDataFreshnessStatus.Fresh, eurUsd.Status);
        Assert.Equal(5, eurUsd.AgeMinutes);
    }

    [Fact]
    public async Task GetStatusAsync_WhenLatestCandleExceedsIntervalAndGrace_ReturnsStale()
    {
        var now = new DateTimeOffset(2026, 8, 31, 10, 21, 0, TimeSpan.Zero);
        var service = CreateService(now, [Candle("EURUSD", Timeframe.M15, 9, 45)]);

        var result = await service.GetStatusAsync(CancellationToken.None);

        var eurUsd = Assert.Single(result.Series, series =>
            series.Instrument == "EURUSD" && series.Timeframe == Timeframe.M15);
        Assert.Equal(MarketDataFreshnessStatus.Stale, eurUsd.Status);
    }

    [Fact]
    public async Task GetStatusAsync_WithMissingTradingInterval_ReturnsGapDetected()
    {
        var now = new DateTimeOffset(2026, 8, 31, 10, 5, 0, TimeSpan.Zero);
        var observations = new[]
        {
            Candle("EURUSD", Timeframe.M15, 9, 15),
            Candle("EURUSD", Timeframe.M15, 9, 45)
        };
        var service = CreateService(now, observations);

        var result = await service.GetStatusAsync(CancellationToken.None);

        var eurUsd = Assert.Single(result.Series, series =>
            series.Instrument == "EURUSD" && series.Timeframe == Timeframe.M15);
        Assert.Equal(MarketDataFreshnessStatus.GapDetected, eurUsd.Status);
        Assert.Equal(1, eurUsd.GapCount);
        Assert.Equal(MarketDataFreshnessStatus.GapDetected, result.Status);
    }

    [Fact]
    public async Task GetStatusAsync_WeekendClosureDoesNotCreateSyntheticGap()
    {
        var now = new DateTimeOffset(2026, 8, 30, 21, 0, 0, TimeSpan.Zero);
        var observations = new[]
        {
            Observation("EURUSD", Timeframe.M15, new DateTimeOffset(2026, 8, 21, 21, 45, 0, TimeSpan.Zero)),
            Observation("EURUSD", Timeframe.M15, new DateTimeOffset(2026, 8, 23, 22, 0, 0, TimeSpan.Zero))
        };
        var service = CreateService(now, observations);

        var result = await service.GetStatusAsync(CancellationToken.None);

        var eurUsd = Assert.Single(result.Series, series =>
            series.Instrument == "EURUSD" && series.Timeframe == Timeframe.M15);
        Assert.Equal(0, eurUsd.GapCount);
        Assert.Equal(MarketDataFreshnessStatus.MarketClosed, eurUsd.Status);
    }

    [Theory]
    [InlineData(2026, 8, 30, 21, 59, false)]
    [InlineData(2026, 8, 30, 22, 0, true)]
    [InlineData(2026, 9, 4, 21, 59, true)]
    [InlineData(2026, 9, 4, 22, 0, false)]
    public void IsOpen_UsesCanonicalWeeklyUtcWindow(
        int year,
        int month,
        int day,
        int hour,
        int minute,
        bool expected)
    {
        var time = new DateTimeOffset(year, month, day, hour, minute, 0, TimeSpan.Zero);

        Assert.Equal(expected, ForexMarketSchedule.IsOpen(time));
    }

    private static MarketDataStatusService CreateService(
        DateTimeOffset now,
        IReadOnlyCollection<CandleObservation>? observations = null) =>
        new(
            new StubReadRepository(observations ?? []),
            new FixedTimeProvider(now));

    private static CandleObservation Candle(string instrument, Timeframe timeframe, int hour, int minute) =>
        Observation(
            instrument,
            timeframe,
            new DateTimeOffset(2026, 8, 31, hour, minute, 0, TimeSpan.Zero));

    private static CandleObservation Observation(
        string instrument,
        Timeframe timeframe,
        DateTimeOffset openTime) =>
        new(instrument, timeframe, openTime, openTime.AddMinutes((int)timeframe));

    private sealed class StubReadRepository(IReadOnlyCollection<CandleObservation> observations)
        : IMarketDataReadRepository
    {
        public Task<IReadOnlyCollection<CandleObservation>> GetFinalCandlesSinceAsync(
            DateTimeOffset since,
            CancellationToken cancellationToken) =>
            Task.FromResult(observations);
    }

    private sealed class FixedTimeProvider(DateTimeOffset now) : TimeProvider
    {
        public override DateTimeOffset GetUtcNow() => now;
    }
}
