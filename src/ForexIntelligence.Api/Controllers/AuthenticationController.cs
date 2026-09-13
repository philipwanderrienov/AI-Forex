using ForexIntelligence.Api.Authentication;
using ForexIntelligence.Api.Models.Requests.Authentication;
using ForexIntelligence.Api.Models.Responses.Authentication;
using ForexIntelligence.Application.Interfaces.Repositories;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.RateLimiting;

namespace ForexIntelligence.Api.Controllers;

[ApiController]
[Route("api/auth")]
public sealed class AuthenticationController(
    IUserRepository userRepository,
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
        var user = await userRepository.GetByUsernameAsync(request.Username, cancellationToken);
        if (user is null
            || !user.IsActive
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
