using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace SmartParking.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class AddVehicleInfoToPenalty : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AlterColumn<Guid>(
                name: "ParkingSessionId",
                table: "Penalties",
                type: "uniqueidentifier",
                nullable: true,
                oldClrType: typeof(Guid),
                oldType: "uniqueidentifier");

            migrationBuilder.AddColumn<string>(
                name: "PlateNumber",
                table: "Penalties",
                type: "nvarchar(max)",
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "QrCode",
                table: "Penalties",
                type: "nvarchar(max)",
                nullable: true);

            migrationBuilder.AddColumn<Guid>(
                name: "VehicleId",
                table: "Penalties",
                type: "uniqueidentifier",
                nullable: true);

            migrationBuilder.CreateIndex(
                name: "IX_Penalties_VehicleId",
                table: "Penalties",
                column: "VehicleId");

            migrationBuilder.AddForeignKey(
                name: "FK_Penalties_Vehicles_VehicleId",
                table: "Penalties",
                column: "VehicleId",
                principalTable: "Vehicles",
                principalColumn: "Id");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_Penalties_Vehicles_VehicleId",
                table: "Penalties");

            migrationBuilder.DropIndex(
                name: "IX_Penalties_VehicleId",
                table: "Penalties");

            migrationBuilder.DropColumn(
                name: "PlateNumber",
                table: "Penalties");

            migrationBuilder.DropColumn(
                name: "QrCode",
                table: "Penalties");

            migrationBuilder.DropColumn(
                name: "VehicleId",
                table: "Penalties");

            migrationBuilder.AlterColumn<Guid>(
                name: "ParkingSessionId",
                table: "Penalties",
                type: "uniqueidentifier",
                nullable: false,
                defaultValue: new Guid("00000000-0000-0000-0000-000000000000"),
                oldClrType: typeof(Guid),
                oldType: "uniqueidentifier",
                oldNullable: true);
        }
    }
}
