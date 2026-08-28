using ForexIntelligence.Domain.Enums;

namespace ForexIntelligence.Application.Models;

public sealed record IngestCandleBatchRequest(
    string BatchId,
    string SourceInstanceId,
    long Sequence,
    string Checksum,
    IReadOnlyCollection<IngestCandleRecord> Records);

public sealed record IngestCandleRecord(
    string Instrument,
    Timeframe Timeframe,
    DateTimeOffset OpenTime,
    DateTimeOffset CloseTime,
    decimal Open,
    decimal High,
    decimal Low,
    decimal Close,
    long TickVolume,
    CandleStatus Status);

public enum BatchIngestionStatus
{
    Accepted,
    Duplicate,
    Conflict
}

public sealed record BatchIngestionResult(BatchIngestionStatus Status, string BatchId, int StoredRecords);
