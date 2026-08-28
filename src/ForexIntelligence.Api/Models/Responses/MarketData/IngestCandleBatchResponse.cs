namespace ForexIntelligence.Api.Models.Responses.MarketData;

public sealed record IngestCandleBatchResponse(string Status, string BatchId, int StoredRecords);
