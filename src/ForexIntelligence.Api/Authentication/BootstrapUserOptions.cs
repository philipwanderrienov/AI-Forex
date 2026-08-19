namespace ForexIntelligence.Api.Authentication;

public sealed class BootstrapUserOptions
{
    public const string SectionName = "BootstrapUser";

    public string Username { get; init; } = string.Empty;

    public string PasswordHash { get; init; } = string.Empty;

    public string Role { get; init; } = "USER";
}
