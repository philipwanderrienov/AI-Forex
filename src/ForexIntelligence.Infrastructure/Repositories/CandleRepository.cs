using ForexIntelligence.Application.Interfaces.Repositories;
using ForexIntelligence.Domain.Entities;
using ForexIntelligence.Infrastructure.Data;

namespace ForexIntelligence.Infrastructure.Repositories;

public sealed class CandleRepository(ForexDbContext dbContext) : ICandleRepository
{
    public async Task AddAsync(Candle candle, CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(candle);
        await dbContext.Candles.AddAsync(candle, cancellationToken);
        await dbContext.SaveChangesAsync(cancellationToken);
    }
}
