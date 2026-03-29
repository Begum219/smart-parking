using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace SmartParking.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class AddPenaltyAndParkingEnhancements : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<TimeSpan>(
                name: "EndTime",
                table: "PricingRules",
                type: "time",
                nullable: true);

            migrationBuilder.AddColumn<bool>(
                name: "IsSpecialDay",
                table: "PricingRules",
                type: "bit",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<bool>(
                name: "IsWeekendRate",
                table: "PricingRules",
                type: "bit",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<decimal>(
                name: "SpaceTypeMultiplier",
                table: "PricingRules",
                type: "decimal(5,2)",
                precision: 5,
                scale: 2,
                nullable: false,
                defaultValue: 0m);

            migrationBuilder.AddColumn<decimal>(
                name: "SpecialDayMultiplier",
                table: "PricingRules",
                type: "decimal(5,2)",
                precision: 5,
                scale: 2,
                nullable: false,
                defaultValue: 0m);

            migrationBuilder.AddColumn<TimeSpan>(
                name: "StartTime",
                table: "PricingRules",
                type: "time",
                nullable: true);

            migrationBuilder.AddColumn<decimal>(
                name: "WeekendMultiplier",
                table: "PricingRules",
                type: "decimal(5,2)",
                precision: 5,
                scale: 2,
                nullable: false,
                defaultValue: 0m);

            migrationBuilder.AddColumn<int>(
                name: "Column",
                table: "ParkingSpaces",
                type: "int",
                nullable: false,
                defaultValue: 1);

            migrationBuilder.AddColumn<int>(
                name: "CoordinateX",
                table: "ParkingSpaces",
                type: "int",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.AddColumn<int>(
                name: "CoordinateY",
                table: "ParkingSpaces",
                type: "int",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.AddColumn<int>(
                name: "DistanceFromEntrance",
                table: "ParkingSpaces",
                type: "int",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.AddColumn<int>(
                name: "Height",
                table: "ParkingSpaces",
                type: "int",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.AddColumn<string>(
                name: "NavigationInstructions",
                table: "ParkingSpaces",
                type: "nvarchar(500)",
                maxLength: 500,
                nullable: true);

            migrationBuilder.AddColumn<int>(
                name: "Row",
                table: "ParkingSpaces",
                type: "int",
                nullable: false,
                defaultValue: 1);

            migrationBuilder.AddColumn<string>(
                name: "Section",
                table: "ParkingSpaces",
                type: "nvarchar(10)",
                maxLength: 10,
                nullable: false,
                defaultValue: "A");

            migrationBuilder.AddColumn<int>(
                name: "Width",
                table: "ParkingSpaces",
                type: "int",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.CreateTable(
                name: "Penalties",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uniqueidentifier", nullable: false),
                    ParkingSessionId = table.Column<Guid>(type: "uniqueidentifier", nullable: false),
                    ViolationType = table.Column<string>(type: "nvarchar(50)", maxLength: 50, nullable: false),
                    Amount = table.Column<decimal>(type: "decimal(10,2)", precision: 10, scale: 2, nullable: false),
                    IssuedAt = table.Column<DateTime>(type: "datetime2", nullable: false),
                    IsPaid = table.Column<bool>(type: "bit", nullable: false),
                    PaidAt = table.Column<DateTime>(type: "datetime2", nullable: true),
                    Description = table.Column<string>(type: "nvarchar(500)", maxLength: 500, nullable: false),
                    ImageUrl = table.Column<string>(type: "nvarchar(max)", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "datetime2", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "datetime2", nullable: false),
                    IsDeleted = table.Column<bool>(type: "bit", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Penalties", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Penalties_ParkingSessions_ParkingSessionId",
                        column: x => x.ParkingSessionId,
                        principalTable: "ParkingSessions",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateIndex(
                name: "IX_Penalties_ParkingSessionId",
                table: "Penalties",
                column: "ParkingSessionId");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "Penalties");

            migrationBuilder.DropColumn(
                name: "EndTime",
                table: "PricingRules");

            migrationBuilder.DropColumn(
                name: "IsSpecialDay",
                table: "PricingRules");

            migrationBuilder.DropColumn(
                name: "IsWeekendRate",
                table: "PricingRules");

            migrationBuilder.DropColumn(
                name: "SpaceTypeMultiplier",
                table: "PricingRules");

            migrationBuilder.DropColumn(
                name: "SpecialDayMultiplier",
                table: "PricingRules");

            migrationBuilder.DropColumn(
                name: "StartTime",
                table: "PricingRules");

            migrationBuilder.DropColumn(
                name: "WeekendMultiplier",
                table: "PricingRules");

            migrationBuilder.DropColumn(
                name: "Column",
                table: "ParkingSpaces");

            migrationBuilder.DropColumn(
                name: "CoordinateX",
                table: "ParkingSpaces");

            migrationBuilder.DropColumn(
                name: "CoordinateY",
                table: "ParkingSpaces");

            migrationBuilder.DropColumn(
                name: "DistanceFromEntrance",
                table: "ParkingSpaces");

            migrationBuilder.DropColumn(
                name: "Height",
                table: "ParkingSpaces");

            migrationBuilder.DropColumn(
                name: "NavigationInstructions",
                table: "ParkingSpaces");

            migrationBuilder.DropColumn(
                name: "Row",
                table: "ParkingSpaces");

            migrationBuilder.DropColumn(
                name: "Section",
                table: "ParkingSpaces");

            migrationBuilder.DropColumn(
                name: "Width",
                table: "ParkingSpaces");
        }
    }
}
