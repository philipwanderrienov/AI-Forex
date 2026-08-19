using ForexIntelligence.Domain.Entities;
using ForexIntelligence.Domain.Enums;
using ForexIntelligence.Infrastructure.Data;
using ForexIntelligence.Infrastructure.Repositories;
using Microsoft.EntityFrameworkCore;

namespace ForexIntelligence.IntegrationTests;

public sealed class PostgreSqlPersistenceTests
{
    [Fact]
    public async Task Migration_and_candle_repository_work_with_real_PostgreSQL()
    {
        var connectionString = Environment.GetEnvironmentVariable("FOREX_TEST_POSTGRESQL");
        if (string.IsNullOrWhiteSpace(connectionString))
        {
            return;
        }

        var options = new DbContextOptionsBuilder<ForexDbContext>()
            .UseNpgsql(connectionString)
            .Options;

        await using var dbContext = new ForexDbContext(options);
        await dbContext.Database.MigrateAsync();

        var openTime = DateTimeOffset.UtcNow
            .AddMinutes(-15)
            .AddTicks(-(DateTimeOffset.UtcNow.Ticks % TimeSpan.TicksPerSecond));
        var candle = Candle.Create(
            "EURUSD",
            Timeframe.M15,
            openTime,
            openTime.AddMinutes(15),
            1.1000m,
            1.1020m,
            1.0990m,
            1.1010m,
            123,
            CandleStatus.Final);

        var repository = new CandleRepository(dbContext);
        await repository.AddAsync(candle, CancellationToken.None);

        var storedCandle = await dbContext.Candles
            .AsNoTracking()
            .SingleAsync(value => value.Id == candle.Id, CancellationToken.None);

        Assert.Equal("EURUSD", storedCandle.Instrument);
        Assert.Equal(CandleStatus.Final, storedCandle.Status);
        Assert.Equal(1.1010m, storedCandle.Close);
    }
}
