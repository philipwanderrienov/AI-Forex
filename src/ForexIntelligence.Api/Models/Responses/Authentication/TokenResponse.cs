namespace ForexIntelligence.Api.Models.Responses.Authentication;

public sealed record TokenResponse(
    string TokenType,
    string AccessToken,
    DateTimeOffset AccessTokenExpiresAt,
    string RefreshToken,
    DateTimeOffset RefreshTokenExpiresAt);
