using ForexIntelligence.Application.Models.Authentication;

namespace ForexIntelligence.Application.Interfaces.Repositories;

public interface IRefreshTokenRepository
{
    Task StoreAsync(
        string token,
        RefreshTokenSession session,
        DateTimeOffset createdAt,
        CancellationToken cancellationToken);

    Task<RefreshTokenRotationResult> RotateAsync(
        string currentToken,
        string replacementToken,
        DateTimeOffset replacementExpiresAt,
        DateTimeOffset now,
        CancellationToken cancellationToken);

    Task RevokeAsync(
        string token,
        DateTimeOffset revokedAt,
        CancellationToken cancellationToken);

    Task<int> DeleteExpiredAsync(
        DateTimeOffset cutoff,
        CancellationToken cancellationToken);
}
