using System.Data;
using System.Security.Cryptography;
using System.Text;
using ForexIntelligence.Application.Interfaces.Repositories;
using ForexIntelligence.Application.Models.Authentication;
using ForexIntelligence.Infrastructure.Authentication;
using ForexIntelligence.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace ForexIntelligence.Infrastructure.Repositories;

public sealed class RefreshTokenRepository(ForexDbContext dbContext) : IRefreshTokenRepository
{
    public async Task StoreAsync(
        string token,
        RefreshTokenSession session,
        DateTimeOffset createdAt,
        CancellationToken cancellationToken)
    {
        dbContext.RefreshTokens.Add(CreateRecord(token, session, createdAt));
        await dbContext.SaveChangesAsync(cancellationToken);
    }

    public async Task<RefreshTokenRotationResult> RotateAsync(
        string currentToken,
        string replacementToken,
        DateTimeOffset replacementExpiresAt,
        DateTimeOffset now,
        CancellationToken cancellationToken)
    {
        await using var transaction = await dbContext.Database.BeginTransactionAsync(
            IsolationLevel.Serializable,
            cancellationToken);
        var currentHash = Hash(currentToken);
        var current = await dbContext.RefreshTokens.SingleOrDefaultAsync(
            token => token.TokenHash == currentHash,
            cancellationToken);

        if (current is null)
        {
            return new RefreshTokenRotationResult(RefreshTokenRotationStatus.Invalid);
        }

        if (current.ConsumedAt is not null || current.RevokedAt is not null)
        {
            await RevokeFamilyAsync(current.FamilyId, now, cancellationToken);
            await transaction.CommitAsync(cancellationToken);
            return new RefreshTokenRotationResult(RefreshTokenRotationStatus.ReuseDetected);
        }

        if (current.ExpiresAt <= now)
        {
            current.RevokedAt = now;
            await dbContext.SaveChangesAsync(cancellationToken);
            await transaction.CommitAsync(cancellationToken);
            return new RefreshTokenRotationResult(RefreshTokenRotationStatus.Expired);
        }

        current.ConsumedAt = now;
        current.ReplacedByTokenHash = Hash(replacementToken);
        var boundedReplacementExpiry = replacementExpiresAt < current.ExpiresAt
            ? replacementExpiresAt
            : current.ExpiresAt;
        var replacementSession = new RefreshTokenSession(
            current.FamilyId,
            current.Username,
            current.Role,
            boundedReplacementExpiry);
        dbContext.RefreshTokens.Add(CreateRecord(replacementToken, replacementSession, now));
        await dbContext.SaveChangesAsync(cancellationToken);
        await transaction.CommitAsync(cancellationToken);

        return new RefreshTokenRotationResult(
            RefreshTokenRotationStatus.Succeeded,
            replacementSession);
    }

    public async Task RevokeAsync(
        string token,
        DateTimeOffset revokedAt,
        CancellationToken cancellationToken)
    {
        var tokenHash = Hash(token);
        var record = await dbContext.RefreshTokens.SingleOrDefaultAsync(
            item => item.TokenHash == tokenHash,
            cancellationToken);
        if (record is not null)
        {
            await RevokeFamilyAsync(record.FamilyId, revokedAt, cancellationToken);
        }
    }

    public Task<int> DeleteExpiredAsync(
        DateTimeOffset cutoff,
        CancellationToken cancellationToken)
    {
        return dbContext.RefreshTokens
            .Where(token => token.ExpiresAt < cutoff)
            .ExecuteDeleteAsync(cancellationToken);
    }

    private async Task RevokeFamilyAsync(
        Guid familyId,
        DateTimeOffset revokedAt,
        CancellationToken cancellationToken)
    {
        await dbContext.RefreshTokens
            .Where(token => token.FamilyId == familyId && token.RevokedAt == null)
            .ExecuteUpdateAsync(
                setters => setters.SetProperty(token => token.RevokedAt, revokedAt),
                cancellationToken);
    }

    private static RefreshTokenRecord CreateRecord(
        string token,
        RefreshTokenSession session,
        DateTimeOffset createdAt) => new()
        {
            Id = Guid.NewGuid(),
            TokenHash = Hash(token),
            FamilyId = session.FamilyId,
            Username = session.Username,
            Role = session.Role,
            CreatedAt = createdAt,
            ExpiresAt = session.ExpiresAt
        };

    private static string Hash(string token) =>
        Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(token)));
}
