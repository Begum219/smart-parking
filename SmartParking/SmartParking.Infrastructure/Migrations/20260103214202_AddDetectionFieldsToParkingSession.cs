using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace SmartParking.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class AddDetectionFieldsToParkingSession : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<double>(
                name: "Confidence",
                table: "ParkingSessions",
                type: "float",
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "DetectedPlateNumber",
                table: "ParkingSessions",
                type: "nvarchar(max)",
                nullable: true);

            migrationBuilder.AddColumn<int>(
                name: "DetectionVehicleId",
                table: "ParkingSessions",
                type: "int",
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "QrCode",
                table: "ParkingSessions",
                type: "nvarchar(max)",
                nullable: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "Confidence",
                table: "ParkingSessions");

            migrationBuilder.DropColumn(
                name: "DetectedPlateNumber",
                table: "ParkingSessions");

            migrationBuilder.DropColumn(
                name: "DetectionVehicleId",
                table: "ParkingSessions");

            migrationBuilder.DropColumn(
                name: "QrCode",
                table: "ParkingSessions");
        }
    }
}
