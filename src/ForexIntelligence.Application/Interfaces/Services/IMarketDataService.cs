using ForexIntelligence.Application.Models;

namespace ForexIntelligence.Application.Interfaces.Services;

public interface IMarketDataService
{
    Task<Guid> StoreCandleAsync(
        StoreCandleRequest request,
        CancellationToken cancellationToken);

    Task<BatchIngestionResult> IngestBatchAsync(
        IngestCandleBatchRequest request,
        CancellationToken cancellationToken);
}
