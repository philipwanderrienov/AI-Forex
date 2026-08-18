using ForexIntelligence.Api.Models.Responses.System;
using Microsoft.AspNetCore.Mvc;

namespace ForexIntelligence.Api.Controllers;

[ApiController]
[Route("api/system-status")]
public sealed class SystemStatusController(TimeProvider timeProvider) : ControllerBase
{
    [HttpGet]
    [ProducesResponseType<SystemStatusResponse>(StatusCodes.Status200OK)]
    public ActionResult<SystemStatusResponse> Get()
    {
        return Ok(new SystemStatusResponse(
            "Forex Intelligence API",
            "healthy",
            timeProvider.GetUtcNow()));
    }
}
