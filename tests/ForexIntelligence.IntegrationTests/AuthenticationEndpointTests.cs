using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;

namespace ForexIntelligence.IntegrationTests;

public sealed class AuthenticationEndpointTests : IClassFixture<TestWebApplicationFactory>
{
    private readonly HttpClient _client;

    public AuthenticationEndpointTests(TestWebApplicationFactory factory)
    {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task Login_WithValidCredentials_ReturnsTokenThatAuthorizesUserEndpoint()
    {
        var login = await LoginAsync();
        var accessToken = login.GetProperty("accessToken").GetString();
        Assert.False(string.IsNullOrWhiteSpace(accessToken));

        using var request = new HttpRequestMessage(HttpMethod.Get, "/api/system-status");
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", accessToken);
        var response = await _client.SendAsync(request);

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
    }

    [Fact]
    public async Task Login_WithInvalidCredentials_ReturnsUnauthorized()
    {
        var response = await _client.PostAsJsonAsync(
            "/api/auth/login",
            new { username = TestWebApplicationFactory.Username, password = "wrong-password" });

        Assert.Equal(HttpStatusCode.Unauthorized, response.StatusCode);
    }

    [Fact]
    public async Task Refresh_RotatesTokenAndRejectsReuse()
    {
        var login = await LoginAsync();
        var refreshToken = login.GetProperty("refreshToken").GetString();
        Assert.False(string.IsNullOrWhiteSpace(refreshToken));

        var firstRefresh = await _client.PostAsJsonAsync(
            "/api/auth/refresh",
            new { refreshToken });
        firstRefresh.EnsureSuccessStatusCode();
        using var firstRefreshDocument = JsonDocument.Parse(
            await firstRefresh.Content.ReadAsStringAsync());
        var replacementToken = firstRefreshDocument.RootElement
            .GetProperty("refreshToken")
            .GetString();
        var reusedRefresh = await _client.PostAsJsonAsync(
            "/api/auth/refresh",
            new { refreshToken });
        var revokedReplacement = await _client.PostAsJsonAsync(
            "/api/auth/refresh",
            new { refreshToken = replacementToken });

        Assert.Equal(HttpStatusCode.OK, firstRefresh.StatusCode);
        Assert.Equal(HttpStatusCode.Unauthorized, reusedRefresh.StatusCode);
        Assert.Equal(HttpStatusCode.Unauthorized, revokedReplacement.StatusCode);
    }

    private async Task<JsonElement> LoginAsync()
    {
        var response = await _client.PostAsJsonAsync(
            "/api/auth/login",
            new
            {
                username = TestWebApplicationFactory.Username,
                password = TestWebApplicationFactory.Password
            });
        response.EnsureSuccessStatusCode();
        using var document = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
        return document.RootElement.Clone();
    }
}
