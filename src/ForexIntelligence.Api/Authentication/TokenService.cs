using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using ForexIntelligence.Application.Interfaces.Repositories;
using ForexIntelligence.Application.Models.Authentication;
using Microsoft.Extensions.Options;
using Microsoft.IdentityModel.Tokens;

namespace ForexIntelligence.Api.Authentication;

public interface ITokenService
{
    Task<TokenPair> CreateAsync(
        string username,
        string role,
        CancellationToken cancellationToken);

    Task<TokenPair?> RotateAsync(
        string refreshToken,
        CancellationToken cancellationToken);

    Task RevokeAsync(string refreshToken, CancellationToken cancellationToken);
}

public sealed record TokenPair(
    string AccessToken,
    DateTimeOffset AccessTokenExpiresAt,
    string RefreshToken,
    DateTimeOffset RefreshTokenExpiresAt);

public sealed class TokenService(
    IOptions<JwtOptions> options,
    IRefreshTokenRepository refreshTokenRepository,
    TimeProvider timeProvider) : ITokenService
{
    private readonly JwtOptions _options = options.Value;

    public async Task<TokenPair> CreateAsync(
        string username,
        string role,
        CancellationToken cancellationToken)
    {
        var now = timeProvider.GetUtcNow();
        var refreshExpiresAt = now.AddDays(_options.RefreshTokenDays);
        var refreshToken = Base64UrlEncoder.Encode(RandomNumberGenerator.GetBytes(64));
        await refreshTokenRepository.StoreAsync(
            refreshToken,
            new RefreshTokenSession(Guid.NewGuid(), username, role, refreshExpiresAt),
            now,
            cancellationToken);

        return CreateTokenPair(username, role, refreshToken, refreshExpiresAt, now);
    }

    public async Task<TokenPair?> RotateAsync(
        string refreshToken,
        CancellationToken cancellationToken)
    {
        var now = timeProvider.GetUtcNow();
        var replacementToken = Base64UrlEncoder.Encode(RandomNumberGenerator.GetBytes(64));
        var result = await refreshTokenRepository.RotateAsync(
            refreshToken,
            replacementToken,
            now.AddDays(_options.RefreshTokenDays),
            now,
            cancellationToken);

        return result.Status == RefreshTokenRotationStatus.Succeeded && result.Session is not null
            ? CreateTokenPair(
                result.Session.Username,
                result.Session.Role,
                replacementToken,
                result.Session.ExpiresAt,
                now)
            : null;
    }

    public Task RevokeAsync(string refreshToken, CancellationToken cancellationToken) =>
        refreshTokenRepository.RevokeAsync(
            refreshToken,
            timeProvider.GetUtcNow(),
            cancellationToken);

    private TokenPair CreateTokenPair(
        string username,
        string role,
        string refreshToken,
        DateTimeOffset refreshExpiresAt,
        DateTimeOffset now)
    {
        var accessExpiresAt = now.AddMinutes(_options.AccessTokenMinutes);
        var signingCredentials = new SigningCredentials(
            new SymmetricSecurityKey(Encoding.UTF8.GetBytes(_options.SigningKey)),
            SecurityAlgorithms.HmacSha256);
        var descriptor = new SecurityTokenDescriptor
        {
            Subject = new ClaimsIdentity([
                new Claim(JwtRegisteredClaimNames.Sub, username),
                new Claim(ClaimTypes.Name, username),
                new Claim(ClaimTypes.Role, role),
                new Claim(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString("N"))
            ]),
            Issuer = _options.Issuer,
            Audience = _options.Audience,
            IssuedAt = now.UtcDateTime,
            NotBefore = now.UtcDateTime,
            Expires = accessExpiresAt.UtcDateTime,
            SigningCredentials = signingCredentials
        };
        var accessToken = new JwtSecurityTokenHandler().CreateEncodedJwt(descriptor);

        return new TokenPair(accessToken, accessExpiresAt, refreshToken, refreshExpiresAt);
    }
}
