using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace ForexIntelligence.Infrastructure.Data.Migrations;

/// <inheritdoc />
public partial class AddMarketDataBatches : Migration
{
    /// <inheritdoc />
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.CreateTable(
            name: "market_data_batches",
            columns: table => new
            {
                BatchId = table.Column<string>(type: "character varying(26)", maxLength: 26, nullable: false),
                SourceInstanceId = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: false),
                Sequence = table.Column<long>(type: "bigint", nullable: false),
                Checksum = table.Column<string>(type: "character varying(71)", maxLength: 71, nullable: false),
                RecordCount = table.Column<int>(type: "integer", nullable: false),
                StoredAt = table.Column<DateTimeOffset>(type: "timestamp with time zone", nullable: false)
            },
            constraints: table =>
            {
                table.PrimaryKey("PK_market_data_batches", x => x.BatchId);
            });

        migrationBuilder.CreateIndex(
            name: "IX_market_data_batches_SourceInstanceId_Sequence",
            table: "market_data_batches",
            columns: new[] { "SourceInstanceId", "Sequence" },
            unique: true);
    }

    /// <inheritdoc />
    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropTable(
            name: "market_data_batches");
    }
}
