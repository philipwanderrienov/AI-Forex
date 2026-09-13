namespace ForexIntelligence.Application.Models.Authentication;

public sealed record UserCredential(
    Guid Id,
    string Username,
    string PasswordHash,
    string Role,
    bool IsActive);
