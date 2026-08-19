using System.Net;

namespace ForexIntelligence.IntegrationTests;

public sealed class SystemStatusEndpointTests : IClassFixture<TestWebApplicationFactory>
{
    private readonly HttpClient _client;

    public SystemStatusEndpointTests(TestWebApplicationFactory factory)
    {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task GetSystemStatus_WithoutToken_ReturnsUnauthorized()
    {
        var response = await _client.GetAsync("/api/system-status");

        Assert.Equal(HttpStatusCode.Unauthorized, response.StatusCode);
    }
}
