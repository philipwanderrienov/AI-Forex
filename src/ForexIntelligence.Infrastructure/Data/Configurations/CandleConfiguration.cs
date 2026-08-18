using ForexIntelligence.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace ForexIntelligence.Infrastructure.Data.Configurations;

public sealed class CandleConfiguration : IEntityTypeConfiguration<Candle>
{
    public void Configure(EntityTypeBuilder<Candle> builder)
    {
        builder.ToTable("candles");
        builder.HasKey(candle => candle.Id);
        builder.Property(candle => candle.Instrument).HasMaxLength(12).IsRequired();
        builder.Property(candle => candle.Timeframe).HasConversion<string>().HasMaxLength(4);
        builder.Property(candle => candle.Status).HasConversion<string>().HasMaxLength(12);
        builder.Property(candle => candle.Open).HasPrecision(20, 10);
        builder.Property(candle => candle.High).HasPrecision(20, 10);
        builder.Property(candle => candle.Low).HasPrecision(20, 10);
        builder.Property(candle => candle.Close).HasPrecision(20, 10);

        builder.HasIndex(candle => new
        {
            candle.Instrument,
            candle.Timeframe,
            candle.OpenTime
        })
            .IsUnique();
    }
}
