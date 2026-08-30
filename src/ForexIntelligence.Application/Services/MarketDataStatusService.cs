using ForexIntelligence.Application.Interfaces.Repositories;
using ForexIntelligence.Application.Interfaces.Services;
using ForexIntelligence.Application.Models.MarketData;
using ForexIntelligence.Domain.Enums;

namespace ForexIntelligence.Application.Services;

public sealed class MarketDataStatusService(
    IMarketDataReadRepository repository,
    TimeProvider timeProvider) : IMarketDataStatusService
{
    private const int LookbackDays = 8;
    private const int FreshnessGraceMinutes = 5;
    private static readonly string[] Instruments = ["EURUSD", "GBPUSD", "EURGBP", "EURCHF", "XAUUSD"];
    private static readonly Timeframe[] Timeframes = [Timeframe.M15, Timeframe.H1, Timeframe.H4];

    public async Task<MarketDataStatusSnapshot> GetStatusAsync(CancellationToken cancellationToken)
    {
        var now = timeProvider.GetUtcNow();
        var observations = await repository.GetFinalCandlesSinceAsync(
            now.AddDays(-LookbackDays),
            cancellationToken);
        var marketOpen = ForexMarketSchedule.IsOpen(now);
        var statuses = new List<MarketDataSeriesStatus>(Instruments.Length * Timeframes.Length);

        foreach (var instrument in Instruments)
        {
            foreach (var timeframe in Timeframes)
            {
                var series = observations
                    .Where(candle => candle.Instrument == instrument && candle.Timeframe == timeframe)
                    .OrderBy(candle => candle.OpenTime)
                    .ToArray();
                statuses.Add(EvaluateSeries(instrument, timeframe, series, now, marketOpen));
            }
        }

        return new MarketDataStatusSnapshot(
            OverallStatus(statuses, marketOpen),
            now,
            marketOpen,
            statuses);
    }

    private static MarketDataSeriesStatus EvaluateSeries(
        string instrument,
        Timeframe timeframe,
        CandleObservation[] observations,
        DateTimeOffset now,
        bool marketOpen)
    {
        if (observations.Length == 0)
        {
            return new MarketDataSeriesStatus(
                instrument,
                timeframe,
                MarketDataFreshnessStatus.Unknown,
                null,
                null,
                null,
                0);
        }

        var duration = TimeSpan.FromMinutes((int)timeframe);
        var gapCount = CountExpectedGaps(observations, duration);
        var latest = observations[^1];
        var age = now - latest.CloseTime;
        var status = gapCount > 0
            ? MarketDataFreshnessStatus.GapDetected
            : !marketOpen
                ? MarketDataFreshnessStatus.MarketClosed
                : age > duration.Add(TimeSpan.FromMinutes(FreshnessGraceMinutes))
                    ? MarketDataFreshnessStatus.Stale
                    : MarketDataFreshnessStatus.Fresh;

        return new MarketDataSeriesStatus(
            instrument,
            timeframe,
            status,
            latest.OpenTime,
            latest.CloseTime,
            Math.Round(Math.Max(0, age.TotalMinutes), 3),
            gapCount);
    }

    private static int CountExpectedGaps(
        CandleObservation[] observations,
        TimeSpan duration)
    {
        var gapCount = 0;
        for (var index = 1; index < observations.Length; index++)
        {
            var expectedOpen = observations[index - 1].OpenTime.Add(duration);
            while (expectedOpen < observations[index].OpenTime)
            {
                if (ForexMarketSchedule.IsOpen(expectedOpen))
                {
                    gapCount++;
                }

                expectedOpen = expectedOpen.Add(duration);
            }
        }

        return gapCount;
    }

    private static MarketDataFreshnessStatus OverallStatus(
        IReadOnlyCollection<MarketDataSeriesStatus> statuses,
        bool marketOpen)
    {
        if (statuses.Any(series => series.Status == MarketDataFreshnessStatus.GapDetected))
        {
            return MarketDataFreshnessStatus.GapDetected;
        }

        if (statuses.Any(series => series.Status == MarketDataFreshnessStatus.Stale))
        {
            return MarketDataFreshnessStatus.Stale;
        }

        if (statuses.Any(series => series.Status == MarketDataFreshnessStatus.Unknown))
        {
            return MarketDataFreshnessStatus.Unknown;
        }

        return marketOpen
            ? MarketDataFreshnessStatus.Fresh
            : MarketDataFreshnessStatus.MarketClosed;
    }
}
