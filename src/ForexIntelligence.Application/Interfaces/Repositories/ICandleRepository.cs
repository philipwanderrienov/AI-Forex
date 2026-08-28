using ForexIntelligence.Domain.Entities;

namespace ForexIntelligence.Application.Interfaces.Repositories;

public interface ICandleRepository
{
    Task AddAsync(Candle candle, CancellationToken cancellationToken);

    Task<CandleBatchStoreResult> StoreBatchAsync(
        string batchId,
        string sourceInstanceId,
        long sequence,
        string checksum,
        IReadOnlyCollection<Candle> candles,
        CancellationToken cancellationToken);
}
