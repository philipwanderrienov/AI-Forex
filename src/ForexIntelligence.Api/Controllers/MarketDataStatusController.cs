using ForexIntelligence.Application.Interfaces.Services;
using ForexIntelligence.Application.Models.MarketData;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace ForexIntelligence.Api.Controllers;

[ApiController]
[Authorize(Policy = "USER")]
[Route("api/market-data/status")]
public sealed class MarketDataStatusController(IMarketDataStatusService statusService) : ControllerBase
{
    [HttpGet]
    [ProducesResponseType<MarketDataStatusSnapshot>(StatusCodes.Status200OK)]
    public async Task<ActionResult<MarketDataStatusSnapshot>> Get(CancellationToken cancellationToken) =>
        Ok(await statusService.GetStatusAsync(cancellationToken));
}
