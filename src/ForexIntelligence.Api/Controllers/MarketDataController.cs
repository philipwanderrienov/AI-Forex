using ForexIntelligence.Api.Models.Requests.MarketData;
using ForexIntelligence.Api.Models.Responses.MarketData;
using ForexIntelligence.Application.Interfaces.Services;
using ForexIntelligence.Application.Models;
using Microsoft.AspNetCore.Mvc;

namespace ForexIntelligence.Api.Controllers;

[ApiController]
[Route("api/market-data")]
public sealed class MarketDataController(IMarketDataService marketDataService) : ControllerBase
{
    [HttpPost("candles")]
    [ProducesResponseType<StoreCandleResponse>(StatusCodes.Status202Accepted)]
    [ProducesResponseType<ProblemDetails>(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<StoreCandleResponse>> StoreCandle(
        StoreCandleApiRequest request,
        CancellationToken cancellationToken)
    {
        var applicationRequest = new StoreCandleRequest(
            request.Instrument,
            request.Timeframe,
            request.OpenTime,
            request.CloseTime,
            request.Open,
            request.High,
            request.Low,
            request.Close,
            request.TickVolume,
            request.Status);

        var candleId = await marketDataService.StoreCandleAsync(
            applicationRequest,
            cancellationToken);

        return Accepted(new StoreCandleResponse(candleId));
    }
}
