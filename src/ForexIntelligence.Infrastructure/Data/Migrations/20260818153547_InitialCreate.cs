using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace ForexIntelligence.Infrastructure.Data.Migrations;

/// <inheritdoc />
public partial class InitialCreate : Migration
{
    /// <inheritdoc />
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.CreateTable(
            name: "candles",
            columns: table => new
            {
                Id = table.Column<Guid>(type: "uuid", nullable: false),
                Instrument = table.Column<string>(type: "character varying(12)", maxLength: 12, nullable: false),
                Timeframe = table.Column<string>(type: "character varying(4)", maxLength: 4, nullable: false),
                OpenTime = table.Column<DateTimeOffset>(type: "timestamp with time zone", nullable: false),
                CloseTime = table.Column<DateTimeOffset>(type: "timestamp with time zone", nullable: false),
                Open = table.Column<decimal>(type: "numeric(20,10)", precision: 20, scale: 10, nullable: false),
                High = table.Column<decimal>(type: "numeric(20,10)", precision: 20, scale: 10, nullable: false),
                Low = table.Column<decimal>(type: "numeric(20,10)", precision: 20, scale: 10, nullable: false),
                Close = table.Column<decimal>(type: "numeric(20,10)", precision: 20, scale: 10, nullable: false),
                TickVolume = table.Column<long>(type: "bigint", nullable: false),
                Status = table.Column<string>(type: "character varying(12)", maxLength: 12, nullable: false)
            },
            constraints: table =>
            {
                table.PrimaryKey("PK_candles", x => x.Id);
            });

        migrationBuilder.CreateIndex(
            name: "IX_candles_Instrument_Timeframe_OpenTime",
            table: "candles",
            columns: new[] { "Instrument", "Timeframe", "OpenTime" },
            unique: true);
    }

    /// <inheritdoc />
    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropTable(
            name: "candles");
    }
}
