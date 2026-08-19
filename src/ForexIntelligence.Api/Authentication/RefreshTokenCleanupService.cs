using ForexIntelligence.Application.Interfaces.Repositories;

namespace ForexIntelligence.Api.Authentication;

public sealed partial class RefreshTokenCleanupService(
    IServiceScopeFactory scopeFactory,
    TimeProvider timeProvider,
    ILogger<RefreshTokenCleanupService> logger) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        using var timer = new PeriodicTimer(TimeSpan.FromHours(6), timeProvider);
        while (await timer.WaitForNextTickAsync(stoppingToken))
        {
            await using var scope = scopeFactory.CreateAsyncScope();
            var repository = scope.ServiceProvider.GetRequiredService<IRefreshTokenRepository>();
            var cutoff = timeProvider.GetUtcNow().AddDays(-1);
            var deleted = await repository.DeleteExpiredAsync(cutoff, stoppingToken);
            LogCleanupCompleted(logger, deleted);
        }
    }

    [LoggerMessage(
        EventId = 1100,
        Level = LogLevel.Information,
        Message = "Deleted {DeletedCount} expired refresh-token records")]
    private static partial void LogCleanupCompleted(ILogger logger, int deletedCount);
}
