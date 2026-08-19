using System.Collections.Concurrent;
using ForexIntelligence.Application.Interfaces.Repositories;
using ForexIntelligence.Application.Models.Authentication;

namespace ForexIntelligence.IntegrationTests;

public sealed class InMemoryRefreshTokenRepository : IRefreshTokenRepository
{
    private readonly ConcurrentDictionary<string, Entry> _tokens = new();

    public Task StoreAsync(
        string token,
        RefreshTokenSession session,
        DateTimeOffset createdAt,
        CancellationToken cancellationToken)
    {
        _tokens[token] = new Entry(session);
        return Task.CompletedTask;
    }

    public Task<RefreshTokenRotationResult> RotateAsync(
        string currentToken,
        string replacementToken,
        DateTimeOffset replacementExpiresAt,
        DateTimeOffset now,
        CancellationToken cancellationToken)
    {
        if (!_tokens.TryGetValue(currentToken, out var current))
        {
            return Task.FromResult(new RefreshTokenRotationResult(RefreshTokenRotationStatus.Invalid));
        }

        lock (current)
        {
            if (current.Consumed || current.Revoked)
            {
                foreach (var entry in _tokens.Values.Where(
                    entry => entry.Session.FamilyId == current.Session.FamilyId))
                {
                    entry.Revoked = true;
                }

                return Task.FromResult(
                    new RefreshTokenRotationResult(RefreshTokenRotationStatus.ReuseDetected));
            }

            if (current.Session.ExpiresAt <= now)
            {
                current.Revoked = true;
                return Task.FromResult(
                    new RefreshTokenRotationResult(RefreshTokenRotationStatus.Expired));
            }

            current.Consumed = true;
            var session = current.Session with
            {
                ExpiresAt = replacementExpiresAt < current.Session.ExpiresAt
                    ? replacementExpiresAt
                    : current.Session.ExpiresAt
            };
            _tokens[replacementToken] = new Entry(session);
            return Task.FromResult(
                new RefreshTokenRotationResult(RefreshTokenRotationStatus.Succeeded, session));
        }
    }

    public Task RevokeAsync(
        string token,
        DateTimeOffset revokedAt,
        CancellationToken cancellationToken)
    {
        if (_tokens.TryGetValue(token, out var current))
        {
            foreach (var entry in _tokens.Values.Where(
                entry => entry.Session.FamilyId == current.Session.FamilyId))
            {
                entry.Revoked = true;
            }
        }

        return Task.CompletedTask;
    }

    public Task<int> DeleteExpiredAsync(
        DateTimeOffset cutoff,
        CancellationToken cancellationToken)
    {
        var deleted = 0;
        foreach (var token in _tokens.Where(item => item.Value.Session.ExpiresAt < cutoff))
        {
            deleted += _tokens.TryRemove(token.Key, out _) ? 1 : 0;
        }

        return Task.FromResult(deleted);
    }

    private sealed class Entry(RefreshTokenSession session)
    {
        public RefreshTokenSession Session { get; } = session;

        public bool Consumed { get; set; }

        public bool Revoked { get; set; }
    }
}
