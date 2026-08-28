using ForexIntelligence.Application.Interfaces.Repositories;
using ForexIntelligence.Application.Models;
using ForexIntelligence.Application.Services;
using ForexIntelligence.Domain.Entities;
using ForexIntelligence.Domain.Enums;

namespace ForexIntelligence.Application.Tests;

public sealed class MarketDataServiceTests
{
    [Fact]
    public async Task StoreCandleAsync_PersistsValidatedCandle()
    {
        var repository = new RecordingCandleRepository();
        var service = new MarketDataService(repository);
        var request = new StoreCandleRequest(
            "XAUUSD",
            Timeframe.M15,
            new DateTimeOffset(2026, 8, 18, 8, 0, 0, TimeSpan.Zero),
            new DateTimeOffset(2026, 8, 18, 8, 15, 0, TimeSpan.Zero),
            2500m,
            2510m,
            2495m,
            2508m,
            250,
            CandleStatus.Final);

        var candleId = await service.StoreCandleAsync(request, CancellationToken.None);

        Assert.NotEqual(Guid.Empty, candleId);
        Assert.NotNull(repository.Candle);
        Assert.Equal("XAUUSD", repository.Candle.Instrument);
    }

    private sealed class RecordingCandleRepository : ICandleRepository
    {
        public Candle? Candle { get; private set; }

        public Task AddAsync(Candle candle, CancellationToken cancellationToken)
        {
            Candle = candle;
            return Task.CompletedTask;
        }

        public Task<CandleBatchStoreResult> StoreBatchAsync(
            string batchId,
            string sourceInstanceId,
            long sequence,
            string checksum,
            IReadOnlyCollection<Candle> candles,
            CancellationToken cancellationToken) =>
            Task.FromResult(CandleBatchStoreResult.Stored);
    }
}
