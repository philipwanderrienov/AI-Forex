using ForexIntelligence.Domain.Enums;
using ForexIntelligence.Domain.Exceptions;

namespace ForexIntelligence.Domain.ValueObjects;

public sealed record TradingInstrument
{
    private TradingInstrument(
        string symbol,
        InstrumentType instrumentType,
        string baseAsset,
        string quoteCurrency)
    {
        Symbol = symbol;
        InstrumentType = instrumentType;
        BaseAsset = baseAsset;
        QuoteCurrency = quoteCurrency;
    }

    public string Symbol { get; }

    public InstrumentType InstrumentType { get; }

    public string BaseAsset { get; }

    public string QuoteCurrency { get; }

    public static TradingInstrument FromCanonicalSymbol(string symbol)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(symbol);

        return symbol.Trim().ToUpperInvariant() switch
        {
            "EURUSD" => new("EURUSD", InstrumentType.Forex, "EUR", "USD"),
            "GBPUSD" => new("GBPUSD", InstrumentType.Forex, "GBP", "USD"),
            "EURGBP" => new("EURGBP", InstrumentType.Forex, "EUR", "GBP"),
            "EURCHF" => new("EURCHF", InstrumentType.Forex, "EUR", "CHF"),
            "XAUUSD" => new("XAUUSD", InstrumentType.PreciousMetal, "XAU", "USD"),
            _ => throw new DomainValidationException($"Instrument '{symbol}' tidak termasuk universe MVP.")
        };
    }
}
