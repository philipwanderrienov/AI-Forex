using System.Net;
using Microsoft.AspNetCore.Mvc.Testing;

namespace ForexIntelligence.IntegrationTests;

public sealed class SystemStatusEndpointTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client;

    public SystemStatusEndpointTests(WebApplicationFactory<Program> factory)
    {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task GetSystemStatus_ReturnsOk()
    {
        var response = await _client.GetAsync("/api/system-status");

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
    }
}
