using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace ForexIntelligence.Infrastructure.Data.Configurations;

public sealed class MarketDataBatchRecordConfiguration : IEntityTypeConfiguration<MarketDataBatchRecord>
{
    public void Configure(EntityTypeBuilder<MarketDataBatchRecord> builder)
    {
        builder.ToTable("market_data_batches");
        builder.HasKey(batch => batch.BatchId);
        builder.Property(batch => batch.BatchId).HasMaxLength(26);
        builder.Property(batch => batch.SourceInstanceId).HasMaxLength(64).IsRequired();
        builder.Property(batch => batch.Checksum).HasMaxLength(71).IsRequired();
        builder.HasIndex(batch => new { batch.SourceInstanceId, batch.Sequence }).IsUnique();
    }
}
