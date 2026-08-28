using ForexIntelligence.Application.Interfaces.Repositories;
using ForexIntelligence.Application.Interfaces.Services;
using ForexIntelligence.Application.Models;
using ForexIntelligence.Domain.Entities;

namespace ForexIntelligence.Application.Services;

public sealed class MarketDataService(ICandleRepository candleRepository) : IMarketDataService
{
    public async Task<Guid> StoreCandleAsync(
        StoreCandleRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);

        var candle = Candle.Create(
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

        await candleRepository.AddAsync(candle, cancellationToken);
        return candle.Id;
    }

    public async Task<BatchIngestionResult> IngestBatchAsync(
        IngestCandleBatchRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        ArgumentException.ThrowIfNullOrWhiteSpace(request.BatchId);
        ArgumentException.ThrowIfNullOrWhiteSpace(request.SourceInstanceId);
        ArgumentException.ThrowIfNullOrWhiteSpace(request.Checksum);

        if (request.Sequence < 0 || request.Records.Count is < 1 or > 100)
        {
            throw new ArgumentException("Batch sequence atau jumlah record tidak valid.", nameof(request));
        }

        var candles = request.Records
            .Select(record => Candle.Create(
                record.Instrument,
                record.Timeframe,
                record.OpenTime,
                record.CloseTime,
                record.Open,
                record.High,
                record.Low,
                record.Close,
                record.TickVolume,
                record.Status))
            .ToArray();

        var storeResult = await candleRepository.StoreBatchAsync(
            request.BatchId,
            request.SourceInstanceId,
            request.Sequence,
            request.Checksum,
            candles,
            cancellationToken);

        var status = storeResult switch
        {
            CandleBatchStoreResult.Stored => BatchIngestionStatus.Accepted,
            CandleBatchStoreResult.Duplicate => BatchIngestionStatus.Duplicate,
            _ => BatchIngestionStatus.Conflict
        };
        return new BatchIngestionResult(status, request.BatchId, status == BatchIngestionStatus.Accepted ? candles.Length : 0);
    }
}
