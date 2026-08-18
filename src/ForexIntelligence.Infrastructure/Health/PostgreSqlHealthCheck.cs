using Microsoft.Extensions.Diagnostics.HealthChecks;
using Npgsql;

namespace ForexIntelligence.Infrastructure.Health;

public sealed class PostgreSqlHealthCheck(string connectionString) : IHealthCheck
{
    public async Task<HealthCheckResult> CheckHealthAsync(
        HealthCheckContext context,
        CancellationToken cancellationToken = default)
    {
        try
        {
            await using var connection = new NpgsqlConnection(connectionString);
            await connection.OpenAsync(cancellationToken);

            await using var command = new NpgsqlCommand("SELECT 1", connection);
            var result = await command.ExecuteScalarAsync(cancellationToken);

            return result is 1
                ? HealthCheckResult.Healthy("PostgreSQL siap menerima query.")
                : HealthCheckResult.Unhealthy("PostgreSQL memberikan hasil health query yang tidak valid.");
        }
        catch (Exception exception)
        {
            return HealthCheckResult.Unhealthy(
                "PostgreSQL tidak dapat dihubungi.",
                exception);
        }
    }
}
