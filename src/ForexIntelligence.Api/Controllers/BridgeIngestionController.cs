using System.Globalization;
using ForexIntelligence.Api.Authentication;
using ForexIntelligence.Api.Models.Requests.MarketData;
using ForexIntelligence.Api.Models.Responses.MarketData;
using ForexIntelligence.Application.Interfaces.Services;
using ForexIntelligence.Application.Models;
using ForexIntelligence.Domain.Enums;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace ForexIntelligence.Api.Controllers;

[ApiController]
[Route("api/v1/bridge")]
[Authorize(Policy = BridgeApiKeyOptions.Scheme)]
public sealed class BridgeIngestionController(IMarketDataService marketDataService) : ControllerBase
{
    [HttpPost("candle-batches")]
    [ProducesResponseType<IngestCandleBatchResponse>(StatusCodes.Status202Accepted)]
    [ProducesResponseType<ProblemDetails>(StatusCodes.Status400BadRequest)]
    [ProducesResponseType<ProblemDetails>(StatusCodes.Status409Conflict)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<ActionResult<IngestCandleBatchResponse>> Ingest(
        IngestCandleEnvelopeApiRequest request,
        CancellationToken cancellationToken)
    {
        if (request.SchemaVersion != "mt5-envelope.v1" || request.PayloadType != "CANDLES" ||
            request.Records.Count is < 1 or > 100)
        {
            return BadRequest(new ProblemDetails { Title = "Envelope contract tidak valid." });
        }

        IngestCandleRecord[] records;
        try
        {
            records = request.Records.Select(MapRecord).ToArray();
        }
        catch (FormatException error)
        {
            return BadRequest(new ProblemDetails { Title = "Candle contract tidak valid.", Detail = error.Message });
        }

        var result = await marketDataService.IngestBatchAsync(
            new IngestCandleBatchRequest(
                request.BatchId,
                request.SourceInstanceId,
                request.Sequence,
                request.Checksum,
                records),
            cancellationToken);

        var response = new IngestCandleBatchResponse(
            result.Status.ToString().ToLowerInvariant(),
            result.BatchId,
            result.StoredRecords);
        return result.Status == BatchIngestionStatus.Conflict ? Conflict(response) : Accepted(response);
    }

    private static IngestCandleRecord MapRecord(IngestCandleApiRecord record)
    {
        if (record.SchemaVersion != "candle.v1" || record.Source != "MT5" ||
            !Enum.TryParse<Timeframe>(record.Timeframe, true, out var timeframe) ||
            !Enum.TryParse<CandleStatus>(record.Status, true, out var status))
        {
            throw new FormatException("Schema, source, timeframe, atau status candle tidak valid.");
        }

        return new IngestCandleRecord(
            record.Instrument,
            timeframe,
            record.OpenTime,
            record.CloseTime,
            ParseDecimal(record.Open),
            ParseDecimal(record.High),
            ParseDecimal(record.Low),
            ParseDecimal(record.Close),
            record.TickVolume,
            status);
    }

    private static decimal ParseDecimal(string value) =>
        decimal.TryParse(value, NumberStyles.AllowDecimalPoint, CultureInfo.InvariantCulture, out var parsed)
            ? parsed
            : throw new FormatException("Harga harus berupa decimal string canonical.");
}
