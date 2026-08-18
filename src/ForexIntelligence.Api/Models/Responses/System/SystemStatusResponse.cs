namespace ForexIntelligence.Api.Models.Responses.System;

public sealed record SystemStatusResponse(
    string Service,
    string Status,
    DateTimeOffset UtcNow);
