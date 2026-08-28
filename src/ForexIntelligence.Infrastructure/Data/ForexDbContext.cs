using ForexIntelligence.Domain.Entities;
using ForexIntelligence.Infrastructure.Authentication;
using Microsoft.EntityFrameworkCore;

namespace ForexIntelligence.Infrastructure.Data;

public sealed class ForexDbContext(DbContextOptions<ForexDbContext> options) : DbContext(options)
{
    public DbSet<Candle> Candles => Set<Candle>();

    public DbSet<RefreshTokenRecord> RefreshTokens => Set<RefreshTokenRecord>();

    public DbSet<MarketDataBatchRecord> MarketDataBatches => Set<MarketDataBatchRecord>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(ForexDbContext).Assembly);
    }
}
