using ForexIntelligence.Application.Models.MarketData;

namespace ForexIntelligence.Application.Interfaces.Services;

public interface IMarketDataStatusService
{
    Task<MarketDataStatusSnapshot> GetStatusAsync(CancellationToken cancellationToken);
}
