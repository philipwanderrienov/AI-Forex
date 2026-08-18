namespace ForexIntelligence.Worker;

public sealed partial class Worker(ILogger<Worker> logger) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            LogWorkerHeartbeat(logger, DateTimeOffset.UtcNow);

            await Task.Delay(TimeSpan.FromSeconds(30), stoppingToken);
        }
    }

    [LoggerMessage(
        EventId = 1000,
        Level = LogLevel.Information,
        Message = "Forex Intelligence worker heartbeat at {UtcNow}")]
    private static partial void LogWorkerHeartbeat(
        ILogger logger,
        DateTimeOffset utcNow);
}
