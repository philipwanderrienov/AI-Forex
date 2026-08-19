using System.Text;
using System.Text.Json.Serialization;
using ForexIntelligence.Api.Authentication;
using ForexIntelligence.Application.Interfaces.Services;
using ForexIntelligence.Application.Services;
using ForexIntelligence.Infrastructure;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.Diagnostics.HealthChecks;
using Microsoft.AspNetCore.RateLimiting;
using Microsoft.IdentityModel.Tokens;

if (args.Contains("--hash-password", StringComparer.Ordinal))
{
    Environment.ExitCode = PasswordHashCommand.Run();
    return;
}

var builder = WebApplication.CreateBuilder(args);

var connectionString = builder.Configuration.GetConnectionString("PostgreSql")
    ?? throw new InvalidOperationException(
        "Connection string 'PostgreSql' belum dikonfigurasi.");

builder.Services
    .AddControllers()
    .AddJsonOptions(options =>
        options.JsonSerializerOptions.Converters.Add(new JsonStringEnumConverter()));
builder.Services.AddOpenApi();
builder.Services.AddProblemDetails();
builder.Services.AddHealthChecks();
builder.Services.AddSingleton(TimeProvider.System);
builder.Services
    .AddOptions<JwtOptions>()
    .Bind(builder.Configuration.GetSection(JwtOptions.SectionName))
    .Validate(options => !string.IsNullOrWhiteSpace(options.Issuer), "Jwt:Issuer wajib diisi.")
    .Validate(options => !string.IsNullOrWhiteSpace(options.Audience), "Jwt:Audience wajib diisi.")
    .Validate(options => Encoding.UTF8.GetByteCount(options.SigningKey) >= 32, "Jwt:SigningKey minimal 32 byte.")
    .Validate(options => options.AccessTokenMinutes is > 0 and <= 15, "Access token maksimal 15 menit.")
    .Validate(options => options.RefreshTokenDays is > 0 and <= 7, "Refresh token maksimal 7 hari.")
    .ValidateOnStart();
builder.Services
    .AddOptions<BootstrapUserOptions>()
    .Bind(builder.Configuration.GetSection(BootstrapUserOptions.SectionName))
    .Validate(options => !string.IsNullOrWhiteSpace(options.Username), "BootstrapUser:Username wajib diisi.")
    .Validate(
        options => PasswordHashing.IsValidHash(options.PasswordHash),
        "BootstrapUser:PasswordHash wajib berupa hash PBKDF2-SHA256.")
    .Validate(options => options.Role is "USER" or "ADMIN", "Role harus USER atau ADMIN.")
    .ValidateOnStart();
builder.Services
    .AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer();
builder.Services
    .AddOptions<JwtBearerOptions>(JwtBearerDefaults.AuthenticationScheme)
    .Configure<Microsoft.Extensions.Options.IOptions<JwtOptions>>((options, configuredJwt) =>
    {
        var jwtOptions = configuredJwt.Value;
        options.MapInboundClaims = false;
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidIssuer = jwtOptions.Issuer,
            ValidateAudience = true,
            ValidAudience = jwtOptions.Audience,
            ValidateIssuerSigningKey = true,
            IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtOptions.SigningKey)),
            ValidateLifetime = true,
            ClockSkew = TimeSpan.FromSeconds(30),
            NameClaimType = "name",
            RoleClaimType = "role"
        };
    });
builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("USER", policy => policy.RequireRole("USER", "ADMIN"));
    options.AddPolicy("ADMIN", policy => policy.RequireRole("ADMIN"));
});
builder.Services.AddRateLimiter(options =>
{
    options.RejectionStatusCode = StatusCodes.Status429TooManyRequests;
    options.AddFixedWindowLimiter("login", limiter =>
    {
        limiter.PermitLimit = 5;
        limiter.Window = TimeSpan.FromMinutes(1);
        limiter.QueueLimit = 0;
    });
});
builder.Services.AddScoped<ITokenService, TokenService>();
builder.Services.AddHostedService<RefreshTokenCleanupService>();
builder.Services.AddScoped<IMarketDataService, MarketDataService>();
builder.Services.AddInfrastructure(connectionString);

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}

app.UseHttpsRedirection();

app.UseRateLimiter();
app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();
app.MapHealthChecks("/health");
app.MapHealthChecks(
    "/health/live",
    new HealthCheckOptions
    {
        Predicate = _ => false
    });
app.MapHealthChecks(
    "/health/ready",
    new HealthCheckOptions
    {
        Predicate = registration => registration.Tags.Contains("ready")
    });

app.Run();

public partial class Program;
