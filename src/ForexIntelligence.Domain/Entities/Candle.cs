using ForexIntelligence.Domain.Enums;
using ForexIntelligence.Domain.Exceptions;
using ForexIntelligence.Domain.ValueObjects;

namespace ForexIntelligence.Domain.Entities;

public sealed class Candle
{
    private Candle()
    {
    }

    private Candle(
        Guid id,
        string instrument,
        Timeframe timeframe,
        DateTimeOffset openTime,
        DateTimeOffset closeTime,
        decimal open,
        decimal high,
        decimal low,
        decimal close,
        long tickVolume,
        CandleStatus status)
    {
        Id = id;
        Instrument = instrument;
        Timeframe = timeframe;
        OpenTime = openTime;
        CloseTime = closeTime;
        Open = open;
        High = high;
        Low = low;
        Close = close;
        TickVolume = tickVolume;
        Status = status;
    }

    public Guid Id { get; private set; }

    public string Instrument { get; private set; } = string.Empty;

    public Timeframe Timeframe { get; private set; }

    public DateTimeOffset OpenTime { get; private set; }

    public DateTimeOffset CloseTime { get; private set; }

    public decimal Open { get; private set; }

    public decimal High { get; private set; }

    public decimal Low { get; private set; }

    public decimal Close { get; private set; }

    public long TickVolume { get; private set; }

    public CandleStatus Status { get; private set; }

    public static Candle Create(
        string instrument,
        Timeframe timeframe,
        DateTimeOffset openTime,
        DateTimeOffset closeTime,
        decimal open,
        decimal high,
        decimal low,
        decimal close,
        long tickVolume,
        CandleStatus status)
    {
        var canonicalInstrument = TradingInstrument.FromCanonicalSymbol(instrument);

        if (openTime.Offset != TimeSpan.Zero || closeTime.Offset != TimeSpan.Zero)
        {
            throw new DomainValidationException("Timestamp candle harus menggunakan UTC.");
        }

        if (closeTime <= openTime)
        {
            throw new DomainValidationException("CloseTime harus lebih besar dari OpenTime.");
        }

        if (open <= 0 || high <= 0 || low <= 0 || close <= 0)
        {
            throw new DomainValidationException("Seluruh harga candle harus positif.");
        }

        if (high < Math.Max(open, close) || low > Math.Min(open, close) || high < low)
        {
            throw new DomainValidationException("Nilai OHLC candle tidak valid.");
        }

        if (tickVolume < 0)
        {
            throw new DomainValidationException("Tick volume tidak boleh negatif.");
        }

        return new Candle(
            Guid.NewGuid(),
            canonicalInstrument.Symbol,
            timeframe,
            openTime,
            closeTime,
            open,
            high,
            low,
            close,
            tickVolume,
            status);
    }
}
