namespace ForexIntelligence.Infrastructure.Authentication;

public sealed class UserRecord
{
    public Guid Id { get; set; }

    public string Username { get; set; } = string.Empty;

    public string PasswordHash { get; set; } = string.Empty;

    public string Role { get; set; } = "USER";

    public bool IsActive { get; set; } = true;

    public DateTimeOffset CreatedAt { get; set; }

    public DateTimeOffset UpdatedAt { get; set; }
}
