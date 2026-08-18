using ForexIntelligence.Application.Interfaces.Repositories;
using ForexIntelligence.Application.Interfaces.Services;
using ForexIntelligence.Application.Models;
using ForexIntelligence.Domain.Entities;

namespace ForexIntelligence.Application.Services;

public sealed class MarketDataService(ICandleRepository candleRepository) : IMarketDataService
{
    public async Task<Guid> StoreCandleAsync(
        StoreCandleRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);

        var candle = Candle.Create(
            request.Instrument,
            request.Timeframe,
            request.OpenTime,
            request.CloseTime,
            request.Open,
            request.High,
            request.Low,
            request.Close,
            request.TickVolume,
            request.Status);

        await candleRepository.AddAsync(candle, cancellationToken);
        return candle.Id;
    }
}
