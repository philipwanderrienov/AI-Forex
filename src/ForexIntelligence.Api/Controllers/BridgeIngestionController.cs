using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
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
            request.Records.Count is < 1 or > 100 || request.SentAt.Offset != TimeSpan.Zero ||
            request.Records.Any(record =>
                record.BrokerServerAlias != request.BrokerServerAlias ||
                record.OpenTime.Offset != TimeSpan.Zero ||
                record.CloseTime.Offset != TimeSpan.Zero ||
                record.ReceivedAt.Offset != TimeSpan.Zero) ||
            !ChecksumMatches(request))
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

    private static bool ChecksumMatches(IngestCandleEnvelopeApiRequest request)
    {
        var canonicalRecords = request.Records.Select(record => new SortedDictionary<string, object?>
        {
            ["brokerServerAlias"] = record.BrokerServerAlias,
            ["brokerSymbol"] = record.BrokerSymbol,
            ["close"] = record.Close,
            ["closeTime"] = UtcIso(record.CloseTime),
            ["dataQuality"] = record.DataQuality,
            ["high"] = record.High,
            ["instrument"] = record.Instrument,
            ["low"] = record.Low,
            ["open"] = record.Open,
            ["openTime"] = UtcIso(record.OpenTime),
            ["receivedAt"] = UtcIso(record.ReceivedAt),
            ["schemaVersion"] = record.SchemaVersion,
            ["source"] = record.Source,
            ["status"] = record.Status,
            ["tickVolume"] = record.TickVolume,
            ["timeframe"] = record.Timeframe
        });
        var canonicalJson = JsonSerializer.Serialize(canonicalRecords);
        var expected = "sha256:" + Convert.ToHexStringLower(SHA256.HashData(Encoding.UTF8.GetBytes(canonicalJson)));
        var expectedBytes = Encoding.ASCII.GetBytes(expected);
        var suppliedBytes = Encoding.ASCII.GetBytes(request.Checksum);
        return expectedBytes.Length == suppliedBytes.Length &&
            CryptographicOperations.FixedTimeEquals(expectedBytes, suppliedBytes);
    }

    private static string UtcIso(DateTimeOffset value) =>
        value.ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss'Z'", CultureInfo.InvariantCulture);
}
