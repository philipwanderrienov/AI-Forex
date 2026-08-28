using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using System.Text.Encodings.Web;
using Microsoft.AspNetCore.Authentication;
using Microsoft.Extensions.Options;

namespace ForexIntelligence.Api.Authentication;

public sealed class BridgeApiKeyAuthenticationHandler(
    IOptionsMonitor<AuthenticationSchemeOptions> schemeOptions,
    ILoggerFactory logger,
    UrlEncoder encoder,
    IOptions<BridgeApiKeyOptions> bridgeOptions)
    : AuthenticationHandler<AuthenticationSchemeOptions>(schemeOptions, logger, encoder)
{
    public const string HeaderName = "X-Bridge-Api-Key";

    protected override Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        if (!Request.Headers.TryGetValue(HeaderName, out var suppliedValues))
        {
            return Task.FromResult(AuthenticateResult.NoResult());
        }

        var supplied = suppliedValues.ToString();
        var expected = bridgeOptions.Value.ApiKey;
        var suppliedBytes = Encoding.UTF8.GetBytes(supplied);
        var expectedBytes = Encoding.UTF8.GetBytes(expected);
        if (suppliedBytes.Length != expectedBytes.Length ||
            !CryptographicOperations.FixedTimeEquals(suppliedBytes, expectedBytes))
        {
            return Task.FromResult(AuthenticateResult.Fail("Bridge API key tidak valid."));
        }

        var identity = new ClaimsIdentity(
            [new Claim(ClaimTypes.NameIdentifier, "mt5-bridge")],
            BridgeApiKeyOptions.Scheme);
        var principal = new ClaimsPrincipal(identity);
        var ticket = new AuthenticationTicket(principal, BridgeApiKeyOptions.Scheme);
        return Task.FromResult(AuthenticateResult.Success(ticket));
    }
}
