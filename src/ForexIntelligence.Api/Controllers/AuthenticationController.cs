using ForexIntelligence.Api.Authentication;
using ForexIntelligence.Api.Models.Requests.Authentication;
using ForexIntelligence.Api.Models.Responses.Authentication;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.RateLimiting;
using Microsoft.Extensions.Options;

namespace ForexIntelligence.Api.Controllers;

[ApiController]
[Route("api/auth")]
public sealed class AuthenticationController(
    IOptions<BootstrapUserOptions> userOptions,
    ITokenService tokenService) : ControllerBase
{
    [AllowAnonymous]
    [HttpPost("login")]
    [EnableRateLimiting("login")]
    [ProducesResponseType<TokenResponse>(StatusCodes.Status200OK)]
    [ProducesResponseType<ProblemDetails>(StatusCodes.Status401Unauthorized)]
    public async Task<ActionResult<TokenResponse>> Login(
        LoginRequest request,
        CancellationToken cancellationToken)
    {
        var user = userOptions.Value;
        if (!string.Equals(request.Username, user.Username, StringComparison.Ordinal)
            || !PasswordHashing.Verify(request.Password, user.PasswordHash))
        {
            return Unauthorized();
        }

        var pair = await tokenService.CreateAsync(
            user.Username,
            user.Role,
            cancellationToken);
        return Ok(ToResponse(pair));
    }

    [AllowAnonymous]
    [HttpPost("refresh")]
    [ProducesResponseType<TokenResponse>(StatusCodes.Status200OK)]
    [ProducesResponseType<ProblemDetails>(StatusCodes.Status401Unauthorized)]
    public async Task<ActionResult<TokenResponse>> Refresh(
        RefreshTokenRequest request,
        CancellationToken cancellationToken)
    {
        var pair = await tokenService.RotateAsync(request.RefreshToken, cancellationToken);
        return pair is null ? Unauthorized() : Ok(ToResponse(pair));
    }

    [AllowAnonymous]
    [HttpPost("revoke")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    public async Task<IActionResult> Revoke(
        RefreshTokenRequest request,
        CancellationToken cancellationToken)
    {
        await tokenService.RevokeAsync(request.RefreshToken, cancellationToken);
        return NoContent();
    }

    private static TokenResponse ToResponse(TokenPair pair) => new(
        "Bearer",
        pair.AccessToken,
        pair.AccessTokenExpiresAt,
        pair.RefreshToken,
        pair.RefreshTokenExpiresAt);
}
