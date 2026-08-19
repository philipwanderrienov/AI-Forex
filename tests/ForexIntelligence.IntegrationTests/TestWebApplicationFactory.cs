using ForexIntelligence.Api.Authentication;
using ForexIntelligence.Application.Interfaces.Repositories;
using Microsoft.AspNetCore.DataProtection;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Microsoft.Extensions.Logging;

namespace ForexIntelligence.IntegrationTests;

public sealed class TestWebApplicationFactory : WebApplicationFactory<Program>
{
    public const string Username = "test-user";
    public const string Password = "test-password";

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureLogging(logging =>
        {
            logging.ClearProviders();
        });
        builder.ConfigureServices(services =>
        {
            services.AddDataProtection().UseEphemeralDataProtectionProvider();
            services.RemoveAll<IRefreshTokenRepository>();
            services.AddSingleton<IRefreshTokenRepository, InMemoryRefreshTokenRepository>();
        });
        builder.ConfigureAppConfiguration((_, configuration) =>
        {
            configuration.AddInMemoryCollection(new Dictionary<string, string?>
            {
                ["Jwt:Issuer"] = "ForexIntelligence.Tests",
                ["Jwt:Audience"] = "ForexIntelligence.Tests.Client",
                ["Jwt:SigningKey"] = "integration-test-signing-key-32-bytes-minimum",
                ["Jwt:AccessTokenMinutes"] = "15",
                ["Jwt:RefreshTokenDays"] = "7",
                ["BootstrapUser:Username"] = Username,
                ["BootstrapUser:PasswordHash"] = PasswordHashing.Hash(Password),
                ["BootstrapUser:Role"] = "ADMIN"
            });
        });
    }
}
