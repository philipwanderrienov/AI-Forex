using ForexIntelligence.Domain.Entities;

namespace ForexIntelligence.Application.Interfaces.Repositories;

public interface ICandleRepository
{
    Task AddAsync(Candle candle, CancellationToken cancellationToken);
}
