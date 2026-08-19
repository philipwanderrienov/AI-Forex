using ForexIntelligence.Infrastructure.Authentication;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace ForexIntelligence.Infrastructure.Data.Configurations;

public sealed class RefreshTokenRecordConfiguration : IEntityTypeConfiguration<RefreshTokenRecord>
{
    public void Configure(EntityTypeBuilder<RefreshTokenRecord> builder)
    {
        builder.ToTable("refresh_tokens");
        builder.HasKey(token => token.Id);
        builder.Property(token => token.TokenHash).HasMaxLength(64).IsRequired();
        builder.Property(token => token.Username).HasMaxLength(128).IsRequired();
        builder.Property(token => token.Role).HasMaxLength(16).IsRequired();
        builder.Property(token => token.ReplacedByTokenHash).HasMaxLength(64);
        builder.HasIndex(token => token.TokenHash).IsUnique();
        builder.HasIndex(token => new { token.FamilyId, token.ExpiresAt });
    }
}
