namespace ForexIntelligence.Infrastructure.Data;

public sealed class MarketDataBatchRecord
{
    public string BatchId { get; set; } = string.Empty;

    public string SourceInstanceId { get; set; } = string.Empty;

    public long Sequence { get; set; }

    public string Checksum { get; set; } = string.Empty;

    public int RecordCount { get; set; }

    public DateTimeOffset StoredAt { get; set; }
}
