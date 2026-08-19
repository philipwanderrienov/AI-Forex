using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace ForexIntelligence.Infrastructure.Data.Migrations;

/// <inheritdoc />
public partial class AddRefreshTokens : Migration
{
    /// <inheritdoc />
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.CreateTable(
            name: "refresh_tokens",
            columns: table => new
            {
                Id = table.Column<Guid>(type: "uuid", nullable: false),
                TokenHash = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: false),
                FamilyId = table.Column<Guid>(type: "uuid", nullable: false),
                Username = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false),
                Role = table.Column<string>(type: "character varying(16)", maxLength: 16, nullable: false),
                CreatedAt = table.Column<DateTimeOffset>(type: "timestamp with time zone", nullable: false),
                ExpiresAt = table.Column<DateTimeOffset>(type: "timestamp with time zone", nullable: false),
                ConsumedAt = table.Column<DateTimeOffset>(type: "timestamp with time zone", nullable: true),
                RevokedAt = table.Column<DateTimeOffset>(type: "timestamp with time zone", nullable: true),
                ReplacedByTokenHash = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: true)
            },
            constraints: table =>
            {
                table.PrimaryKey("PK_refresh_tokens", x => x.Id);
            });

        migrationBuilder.CreateIndex(
            name: "IX_refresh_tokens_FamilyId_ExpiresAt",
            table: "refresh_tokens",
            columns: new[] { "FamilyId", "ExpiresAt" });

        migrationBuilder.CreateIndex(
            name: "IX_refresh_tokens_TokenHash",
            table: "refresh_tokens",
            column: "TokenHash",
            unique: true);
    }

    /// <inheritdoc />
    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropTable(
            name: "refresh_tokens");
    }
}
