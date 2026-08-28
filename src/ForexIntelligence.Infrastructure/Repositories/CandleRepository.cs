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
        dbContext.Candles.AddRange(candles);
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
            return concurrent is not null &&
                concurrent.BatchId == batchId &&
                concurrent.SourceInstanceId == sourceInstanceId &&
                concurrent.Sequence == sequence &&
                concurrent.Checksum == checksum &&
                concurrent.RecordCount == candles.Count
                    ? CandleBatchStoreResult.Duplicate
                    : CandleBatchStoreResult.Conflict;
        }
    }
}
