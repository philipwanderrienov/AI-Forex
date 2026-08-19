namespace ForexIntelligence.Infrastructure.Authentication;

public sealed class RefreshTokenRecord
{
    public Guid Id { get; init; }

    public required string TokenHash { get; init; }

    public Guid FamilyId { get; init; }

    public required string Username { get; init; }

    public required string Role { get; init; }

    public DateTimeOffset CreatedAt { get; init; }

    public DateTimeOffset ExpiresAt { get; init; }

    public DateTimeOffset? ConsumedAt { get; set; }

    public DateTimeOffset? RevokedAt { get; set; }

    public string? ReplacedByTokenHash { get; set; }
}
