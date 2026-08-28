namespace ForexIntelligence.Api.Models.Requests.MarketData;

public sealed record IngestCandleEnvelopeApiRequest(
    string SchemaVersion,
    string BatchId,
    string SourceInstanceId,
    string BrokerServerAlias,
    long Sequence,
    DateTimeOffset SentAt,
    string PayloadType,
    IReadOnlyCollection<IngestCandleApiRecord> Records,
    string Checksum);

public sealed record IngestCandleApiRecord(
    string SchemaVersion,
    string Source,
    string BrokerServerAlias,
    string BrokerSymbol,
    string Instrument,
    string Timeframe,
    DateTimeOffset OpenTime,
    DateTimeOffset CloseTime,
    string Open,
    string High,
    string Low,
    string Close,
    long TickVolume,
    string Status,
    DateTimeOffset ReceivedAt,
    string DataQuality);
