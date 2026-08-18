using ForexIntelligence.Application.Interfaces.Services;
using ForexIntelligence.Application.Services;
using ForexIntelligence.Infrastructure;
using ForexIntelligence.Worker;

var builder = Host.CreateApplicationBuilder(args);

var connectionString = builder.Configuration.GetConnectionString("PostgreSql")
    ?? throw new InvalidOperationException(
        "Connection string 'PostgreSql' belum dikonfigurasi.");

builder.Services.AddScoped<IMarketDataService, MarketDataService>();
builder.Services.AddInfrastructure(connectionString);
builder.Services.AddHostedService<Worker>();

var host = builder.Build();
host.Run();
