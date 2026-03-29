using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace SmartParking.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class AddYamukParkFields : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<string>(
                name: "CameraName",
                table: "Penalties",
                type: "nvarchar(max)",
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "DetectionVehicleId",
                table: "Penalties",
                type: "nvarchar(max)",
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "ParkingSpaceIds",
                table: "Penalties",
                type: "nvarchar(max)",
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "ZoneId",
                table: "Penalties",
                type: "nvarchar(max)",
                nullable: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "CameraName",
                table: "Penalties");

            migrationBuilder.DropColumn(
                name: "DetectionVehicleId",
                table: "Penalties");

            migrationBuilder.DropColumn(
                name: "ParkingSpaceIds",
                table: "Penalties");

            migrationBuilder.DropColumn(
                name: "ZoneId",
                table: "Penalties");
        }
    }
}
