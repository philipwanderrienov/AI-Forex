using ForexIntelligence.Application.Interfaces.Repositories;
using ForexIntelligence.Infrastructure.Data;
using ForexIntelligence.Infrastructure.Health;
using ForexIntelligence.Infrastructure.Repositories;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;

namespace ForexIntelligence.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(
        this IServiceCollection services,
        string connectionString)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(connectionString);
        services.AddDbContext<ForexDbContext>(options => options.UseNpgsql(connectionString));
        services.AddScoped<ICandleRepository, CandleRepository>();
        services
            .AddHealthChecks()
            .AddCheck(
                "postgresql",
                new PostgreSqlHealthCheck(connectionString),
                tags: ["ready"]);
        return services;
    }
}
