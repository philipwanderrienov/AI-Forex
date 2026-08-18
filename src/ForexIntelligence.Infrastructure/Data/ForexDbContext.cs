using ForexIntelligence.Domain.Entities;
using Microsoft.EntityFrameworkCore;

namespace ForexIntelligence.Infrastructure.Data;

public sealed class ForexDbContext(DbContextOptions<ForexDbContext> options) : DbContext(options)
{
    public DbSet<Candle> Candles => Set<Candle>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(ForexDbContext).Assembly);
    }
}
