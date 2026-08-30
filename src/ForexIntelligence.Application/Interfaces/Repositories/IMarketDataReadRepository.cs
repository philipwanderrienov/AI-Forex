using ForexIntelligence.Application.Models.MarketData;

namespace ForexIntelligence.Application.Interfaces.Repositories;

public interface IMarketDataReadRepository
{
    Task<IReadOnlyCollection<CandleObservation>> GetFinalCandlesSinceAsync(
        DateTimeOffset since,
        CancellationToken cancellationToken);
}
