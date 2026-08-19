using System.Net;
using System.Net.Http.Json;
using ForexIntelligence.Application.Interfaces.Repositories;
using ForexIntelligence.Domain.Entities;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.AspNetCore.TestHost;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;

namespace ForexIntelligence.IntegrationTests;

public sealed class MarketDataEndpointTests
{
    [Fact]
    public async Task StoreCandle_UsesApplicationServiceAndRepository()
    {
        var repository = new RecordingCandleRepository();
        await using var factory = new TestWebApplicationFactory()
            .WithWebHostBuilder(builder =>
                builder.ConfigureTestServices(services =>
                {
                    services.RemoveAll<ICandleRepository>();
                    services.AddSingleton<ICandleRepository>(repository);
                }));
        using var client = factory.CreateClient();

        var response = await client.PostAsJsonAsync(
            "/api/market-data/candles",
            new
            {
                instrument = "EURUSD",
                timeframe = "H1",
                openTime = "2026-08-18T08:00:00Z",
                closeTime = "2026-08-18T09:00:00Z",
                open = 1.1700m,
                high = 1.1750m,
                low = 1.1680m,
                close = 1.1730m,
                tickVolume = 100,
                status = "Final"
            });

        Assert.Equal(HttpStatusCode.Accepted, response.StatusCode);
        Assert.NotNull(repository.Candle);
        Assert.Equal("EURUSD", repository.Candle.Instrument);
    }

    private sealed class RecordingCandleRepository : ICandleRepository
    {
        public Candle? Candle { get; private set; }

        public Task AddAsync(Candle candle, CancellationToken cancellationToken)
        {
            Candle = candle;
            return Task.CompletedTask;
        }
    }
}
