using System.Net;
using System.Net.Http.Json;
using ForexIntelligence.Api.Authentication;
using ForexIntelligence.Application.Interfaces.Repositories;
using ForexIntelligence.Domain.Entities;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.AspNetCore.TestHost;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;

namespace ForexIntelligence.IntegrationTests;

public sealed class BridgeIngestionEndpointTests
{
    private const string ApiKey = "integration-test-bridge-api-key-at-least-32-bytes";

    [Fact]
    public async Task Ingest_RequiresBridgeApiKey()
    {
        await using var factory = CreateFactory(new RecordingRepository());
        using var client = factory.CreateClient();

        var response = await client.PostAsJsonAsync("/api/v1/bridge/candle-batches", ValidEnvelope());

        Assert.Equal(HttpStatusCode.Unauthorized, response.StatusCode);
    }

    [Theory]
    [InlineData(CandleBatchStoreResult.Stored, HttpStatusCode.Accepted, "accepted", 1)]
    [InlineData(CandleBatchStoreResult.Duplicate, HttpStatusCode.Accepted, "duplicate", 0)]
    [InlineData(CandleBatchStoreResult.Conflict, HttpStatusCode.Conflict, "conflict", 0)]
    public async Task Ingest_MapsIdempotencyResult(
        CandleBatchStoreResult storeResult,
        HttpStatusCode expectedStatus,
        string expectedResult,
        int expectedStoredRecords)
    {
        var repository = new RecordingRepository(storeResult);
        await using var factory = CreateFactory(repository);
        using var client = factory.CreateClient();
        client.DefaultRequestHeaders.Add(BridgeApiKeyAuthenticationHandler.HeaderName, ApiKey);

        var response = await client.PostAsJsonAsync("/api/v1/bridge/candle-batches", ValidEnvelope());
        var body = await response.Content.ReadFromJsonAsync<IngestionResponse>();

        Assert.Equal(expectedStatus, response.StatusCode);
        Assert.NotNull(body);
        Assert.Equal(expectedResult, body.Status);
        Assert.Equal(expectedStoredRecords, body.StoredRecords);
        Assert.Single(repository.Candles);
    }

    private static WebApplicationFactory<Program> CreateFactory(ICandleRepository repository) =>
        new TestWebApplicationFactory().WithWebHostBuilder(builder =>
            builder.ConfigureTestServices(services =>
            {
                services.RemoveAll<ICandleRepository>();
                services.AddSingleton(repository);
            }));

    private static object ValidEnvelope() => new
    {
        schemaVersion = "mt5-envelope.v1",
        batchId = "01J5J5Y22B8NKZ4M6KW7MPNN6C",
        sourceInstanceId = "lubuntu-mt5-primary",
        brokerServerAlias = "demo-primary",
        sequence = 7,
        sentAt = "2026-08-28T08:00:01Z",
        payloadType = "CANDLES",
        checksum = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        records = new[]
        {
            new
            {
                schemaVersion = "candle.v1",
                source = "MT5",
                brokerServerAlias = "demo-primary",
                brokerSymbol = "EURUSD",
                instrument = "EURUSD",
                timeframe = "H1",
                openTime = "2026-08-28T07:00:00Z",
                closeTime = "2026-08-28T08:00:00Z",
                open = "1.17000",
                high = "1.17250",
                low = "1.16950",
                close = "1.17180",
                tickVolume = 1524,
                status = "FINAL",
                receivedAt = "2026-08-28T08:00:01Z",
                dataQuality = "GOOD"
            }
        }
    };

    private sealed record IngestionResponse(string Status, string BatchId, int StoredRecords);

    private sealed class RecordingRepository(CandleBatchStoreResult result = CandleBatchStoreResult.Stored)
        : ICandleRepository
    {
        public IReadOnlyCollection<Candle> Candles { get; private set; } = [];

        public Task AddAsync(Candle candle, CancellationToken cancellationToken) => Task.CompletedTask;

        public Task<CandleBatchStoreResult> StoreBatchAsync(
            string batchId,
            string sourceInstanceId,
            long sequence,
            string checksum,
            IReadOnlyCollection<Candle> candles,
            CancellationToken cancellationToken)
        {
            Candles = candles;
            return Task.FromResult(result);
        }
    }
}
