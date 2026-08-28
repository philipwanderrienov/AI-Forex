namespace ForexIntelligence.Api.Authentication;

public sealed class BridgeApiKeyOptions
{
    public const string SectionName = "BridgeAuthentication";

    public const string Scheme = "BridgeApiKey";

    public string ApiKey { get; init; } = string.Empty;
}
