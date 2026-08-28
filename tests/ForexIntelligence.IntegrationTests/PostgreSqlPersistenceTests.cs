using ForexIntelligence.Application.Interfaces.Repositories;
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

        var batchCandle = Candle.Create(
            "GBPUSD",
            Timeframe.M15,
            openTime.AddMinutes(-15),
            openTime,
            1.3500m,
            1.3540m,
            1.3480m,
            1.3525m,
            456,
            CandleStatus.Final);
        var batchId = "01" + Guid.NewGuid().ToString("N", null)[..24];
        var sourceInstanceId = "postgres-integration-test-" + Guid.NewGuid().ToString("N", null);

        var first = await repository.StoreBatchAsync(
            batchId,
            sourceInstanceId,
            1,
            "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            [batchCandle],
            CancellationToken.None);
        var duplicate = await repository.StoreBatchAsync(
            batchId,
            sourceInstanceId,
            1,
            "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            [batchCandle],
            CancellationToken.None);

        Assert.Equal(CandleBatchStoreResult.Stored, first);
        Assert.Equal(CandleBatchStoreResult.Duplicate, duplicate);
    }

    [Fact]
    public async Task Batch_persistence_handles_identical_overlap_conflict_and_concurrency()
    {
        var connectionString = Environment.GetEnvironmentVariable("FOREX_TEST_POSTGRESQL");
        if (string.IsNullOrWhiteSpace(connectionString))
        {
            return;
        }

        var options = new DbContextOptionsBuilder<ForexDbContext>()
            .UseNpgsql(connectionString)
            .Options;
        var openTime = UniqueOpenTime();
        var existing = CreateCandle("EURGBP", Timeframe.H1, openTime, 0.8600m, 0.8620m, 0.8590m, 0.8610m);

        await using (var seedContext = new ForexDbContext(options))
        {
            await seedContext.Database.MigrateAsync();
            await new CandleRepository(seedContext).AddAsync(existing, CancellationToken.None);
        }

        var overlap = CreateCandle("EURGBP", Timeframe.H1, openTime, 0.8600m, 0.8620m, 0.8590m, 0.8610m);
        var newCandle = CreateCandle(
            "EURGBP",
            Timeframe.H1,
            openTime.AddHours(1),
            0.8610m,
            0.8630m,
            0.8600m,
            0.8620m);
        var mixedBatchId = NewBatchId();

        await using (var mixedContext = new ForexDbContext(options))
        {
            var mixedResult = await new CandleRepository(mixedContext).StoreBatchAsync(
                mixedBatchId,
                "postgres-overlap-test-" + Guid.NewGuid().ToString("N", null),
                1,
                Checksum('b'),
                [overlap, newCandle],
                CancellationToken.None);

            Assert.Equal(CandleBatchStoreResult.Stored, mixedResult);
            Assert.Equal(
                2,
                await mixedContext.Candles.CountAsync(
                    candle => candle.Instrument == "EURGBP" &&
                        candle.Timeframe == Timeframe.H1 &&
                        (candle.OpenTime == openTime || candle.OpenTime == openTime.AddHours(1))));
            Assert.Equal(2, await mixedContext.MarketDataBatches
                .Where(batch => batch.BatchId == mixedBatchId)
                .Select(batch => batch.RecordCount)
                .SingleAsync());
        }

        await using (var conflictContext = new ForexDbContext(options))
        {
            var conflictingOverlap = CreateCandle(
                "EURGBP",
                Timeframe.H1,
                openTime,
                0.8600m,
                0.8640m,
                0.8590m,
                0.8630m);
            var conflictBatchId = NewBatchId();
            var conflictResult = await new CandleRepository(conflictContext).StoreBatchAsync(
                conflictBatchId,
                "postgres-overlap-conflict-" + Guid.NewGuid().ToString("N", null),
                1,
                Checksum('c'),
                [conflictingOverlap],
                CancellationToken.None);

            Assert.Equal(CandleBatchStoreResult.Conflict, conflictResult);
            Assert.False(await conflictContext.MarketDataBatches.AnyAsync(batch => batch.BatchId == conflictBatchId));
        }

        var concurrentOpenTime = openTime.AddDays(1);
        var firstBatchId = NewBatchId();
        var secondBatchId = NewBatchId();
        await using var firstContext = new ForexDbContext(options);
        await using var secondContext = new ForexDbContext(options);
        var firstTask = new CandleRepository(firstContext).StoreBatchAsync(
            firstBatchId,
            "postgres-concurrent-a-" + Guid.NewGuid().ToString("N", null),
            1,
            Checksum('d'),
            [CreateCandle("EURCHF", Timeframe.H4, concurrentOpenTime, 0.9300m, 0.9320m, 0.9290m, 0.9310m)],
            CancellationToken.None);
        var secondTask = new CandleRepository(secondContext).StoreBatchAsync(
            secondBatchId,
            "postgres-concurrent-b-" + Guid.NewGuid().ToString("N", null),
            1,
            Checksum('e'),
            [CreateCandle("EURCHF", Timeframe.H4, concurrentOpenTime, 0.9300m, 0.9320m, 0.9290m, 0.9310m)],
            CancellationToken.None);

        var results = await Task.WhenAll(firstTask, secondTask);
        Assert.All(results, result => Assert.Equal(CandleBatchStoreResult.Stored, result));
        await using var verificationContext = new ForexDbContext(options);
        Assert.Equal(
            1,
            await verificationContext.Candles.CountAsync(candle =>
                candle.Instrument == "EURCHF" &&
                candle.Timeframe == Timeframe.H4 &&
                candle.OpenTime == concurrentOpenTime));
        Assert.Equal(
            2,
            await verificationContext.MarketDataBatches.CountAsync(batch =>
                batch.BatchId == firstBatchId || batch.BatchId == secondBatchId));
    }

    private static Candle CreateCandle(
        string instrument,
        Timeframe timeframe,
        DateTimeOffset openTime,
        decimal open,
        decimal high,
        decimal low,
        decimal close) =>
        Candle.Create(
            instrument,
            timeframe,
            openTime,
            openTime.AddMinutes((int)timeframe),
            open,
            high,
            low,
            close,
            100,
            CandleStatus.Final);

    private static DateTimeOffset UniqueOpenTime()
    {
        var randomMinutes = BitConverter.ToUInt32(Guid.NewGuid().ToByteArray()) % 2_000_000;
        return new DateTimeOffset(2020, 1, 1, 0, 0, 0, TimeSpan.Zero).AddMinutes(randomMinutes);
    }

    private static string NewBatchId() => "01" + Guid.NewGuid().ToString("N", null)[..24];

    private static string Checksum(char value) => "sha256:" + new string(value, 64);
}
