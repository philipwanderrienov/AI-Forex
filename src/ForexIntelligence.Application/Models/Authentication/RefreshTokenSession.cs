namespace ForexIntelligence.Application.Models.Authentication;

public sealed record RefreshTokenSession(
    Guid FamilyId,
    string Username,
    string Role,
    DateTimeOffset ExpiresAt);

public enum RefreshTokenRotationStatus
{
    Succeeded,
    Invalid,
    Expired,
    ReuseDetected
}

public sealed record RefreshTokenRotationResult(
    RefreshTokenRotationStatus Status,
    RefreshTokenSession? Session = null);
