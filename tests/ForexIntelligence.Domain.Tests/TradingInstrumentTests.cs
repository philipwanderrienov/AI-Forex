using ForexIntelligence.Domain.Enums;
using ForexIntelligence.Domain.Exceptions;
using ForexIntelligence.Domain.ValueObjects;

namespace ForexIntelligence.Domain.Tests;

public sealed class TradingInstrumentTests
{
    [Theory]
    [InlineData("EURUSD", InstrumentType.Forex)]
    [InlineData("GBPUSD", InstrumentType.Forex)]
    [InlineData("EURGBP", InstrumentType.Forex)]
    [InlineData("EURCHF", InstrumentType.Forex)]
    [InlineData("XAUUSD", InstrumentType.PreciousMetal)]
    public void FromCanonicalSymbol_WithMvpInstrument_ReturnsInstrument(
        string symbol,
        InstrumentType expectedType)
    {
        var instrument = TradingInstrument.FromCanonicalSymbol(symbol);

        Assert.Equal(symbol, instrument.Symbol);
        Assert.Equal(expectedType, instrument.InstrumentType);
    }

    [Fact]
    public void FromCanonicalSymbol_OutsideMvp_ThrowsDomainValidationException()
    {
        Assert.Throws<DomainValidationException>(() =>
            TradingInstrument.FromCanonicalSymbol("USDJPY"));
    }
}
