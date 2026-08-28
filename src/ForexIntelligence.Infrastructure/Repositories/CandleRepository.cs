using ForexIntelligence.Application.Interfaces.Repositories;
using ForexIntelligence.Domain.Entities;
using ForexIntelligence.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace ForexIntelligence.Infrastructure.Repositories;

public sealed class CandleRepository(ForexDbContext dbContext) : ICandleRepository
{
    public async Task AddAsync(Candle candle, CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(candle);
        await dbContext.Candles.AddAsync(candle, cancellationToken);
        await dbContext.SaveChangesAsync(cancellationToken);
    }

    public async Task<CandleBatchStoreResult> StoreBatchAsync(
        string batchId,
        string sourceInstanceId,
        long sequence,
        string checksum,
        IReadOnlyCollection<Candle> candles,
        CancellationToken cancellationToken) =>
        await StoreBatchAsync(
            batchId,
            sourceInstanceId,
            sequence,
            checksum,
            candles,
            retryAfterConcurrentCandleInsert: true,
            cancellationToken);

    private async Task<CandleBatchStoreResult> StoreBatchAsync(
        string batchId,
        string sourceInstanceId,
        long sequence,
        string checksum,
        IReadOnlyCollection<Candle> candles,
        bool retryAfterConcurrentCandleInsert,
        CancellationToken cancellationToken)
    {
        var existing = await dbContext.MarketDataBatches
            .AsNoTracking()
            .SingleOrDefaultAsync(
                batch => batch.BatchId == batchId ||
                    (batch.SourceInstanceId == sourceInstanceId && batch.Sequence == sequence),
                cancellationToken);

        if (existing is not null)
        {
            return existing.BatchId == batchId &&
                existing.SourceInstanceId == sourceInstanceId &&
                existing.Sequence == sequence &&
                existing.Checksum == checksum &&
                existing.RecordCount == candles.Count
                    ? CandleBatchStoreResult.Duplicate
                    : CandleBatchStoreResult.Conflict;
        }

        var instruments = candles.Select(candle => candle.Instrument).Distinct().ToArray();
        var timeframes = candles.Select(candle => candle.Timeframe).Distinct().ToArray();
        var openTimes = candles.Select(candle => candle.OpenTime).Distinct().ToArray();
        var persistedCandidates = await dbContext.Candles
            .AsNoTracking()
            .Where(candle =>
                instruments.Contains(candle.Instrument) &&
                timeframes.Contains(candle.Timeframe) &&
                openTimes.Contains(candle.OpenTime))
            .ToArrayAsync(cancellationToken);
        var knownByKey = persistedCandidates.ToDictionary(CandleKey.From);
        var newCandles = new List<Candle>(candles.Count);
        foreach (var candle in candles)
        {
            var key = CandleKey.From(candle);
            if (!knownByKey.TryGetValue(key, out var persisted))
            {
                newCandles.Add(candle);
                knownByKey.Add(key, candle);
            }
            else if (!HasSameValues(persisted, candle))
            {
                return CandleBatchStoreResult.Conflict;
            }
        }

        await using var transaction = await dbContext.Database.BeginTransactionAsync(cancellationToken);
        dbContext.MarketDataBatches.Add(new MarketDataBatchRecord
        {
            BatchId = batchId,
            SourceInstanceId = sourceInstanceId,
            Sequence = sequence,
            Checksum = checksum,
            RecordCount = candles.Count,
            StoredAt = DateTimeOffset.UtcNow
        });
        dbContext.Candles.AddRange(newCandles);
        try
        {
            await dbContext.SaveChangesAsync(cancellationToken);
            await transaction.CommitAsync(cancellationToken);
            return CandleBatchStoreResult.Stored;
        }
        catch (DbUpdateException)
        {
            await transaction.RollbackAsync(cancellationToken);
            dbContext.ChangeTracker.Clear();
            var concurrent = await dbContext.MarketDataBatches
                .AsNoTracking()
                .SingleOrDefaultAsync(
                    batch => batch.BatchId == batchId ||
                        (batch.SourceInstanceId == sourceInstanceId && batch.Sequence == sequence),
                    cancellationToken);
            if (concurrent is not null)
            {
                return concurrent.BatchId == batchId &&
                concurrent.SourceInstanceId == sourceInstanceId &&
                concurrent.Sequence == sequence &&
                concurrent.Checksum == checksum &&
                concurrent.RecordCount == candles.Count
                    ? CandleBatchStoreResult.Duplicate
                    : CandleBatchStoreResult.Conflict;
            }

            return retryAfterConcurrentCandleInsert
                ? await StoreBatchAsync(
                    batchId,
                    sourceInstanceId,
                    sequence,
                    checksum,
                    candles,
                    retryAfterConcurrentCandleInsert: false,
                    cancellationToken)
                : CandleBatchStoreResult.Conflict;
        }
    }

    private static bool HasSameValues(Candle left, Candle right) =>
        left.Instrument == right.Instrument &&
        left.Timeframe == right.Timeframe &&
        left.OpenTime == right.OpenTime &&
        left.CloseTime == right.CloseTime &&
        left.Open == right.Open &&
        left.High == right.High &&
        left.Low == right.Low &&
        left.Close == right.Close &&
        left.TickVolume == right.TickVolume &&
        left.Status == right.Status;

    private readonly record struct CandleKey(
        string Instrument,
        ForexIntelligence.Domain.Enums.Timeframe Timeframe,
        DateTimeOffset OpenTime)
    {
        public static CandleKey From(Candle candle) =>
            new(candle.Instrument, candle.Timeframe, candle.OpenTime);
    }
}
