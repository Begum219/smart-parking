using Microsoft.AspNetCore.Mvc;
using SmartParking.Application.DTOs;
using SmartParking.Application.Interfaces;

namespace SmartParking.APII.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class VehicleController : ControllerBase
    {
        private readonly IVehicleService _vehicleService;

        public VehicleController(IVehicleService vehicleService)
        {
            _vehicleService = vehicleService;
        }

        [HttpGet("user/{userId}")]
        public async Task<IActionResult> GetUserVehicles(Guid userId)
        {
            try
            {
                var vehicles = await _vehicleService.GetUserVehiclesAsync(userId);
                return Ok(vehicles);
            }
            catch (Exception ex)
            {
                return BadRequest(new { message = ex.Message });
            }
        }

        [HttpGet("{vehicleId}")]
        public async Task<IActionResult> GetVehicle(Guid vehicleId)
        {
            try
            {
                var vehicle = await _vehicleService.GetVehicleByIdAsync(vehicleId);
                return Ok(vehicle);
            }
            catch (Exception ex)
            {
                return NotFound(new { message = ex.Message });
            }
        }

        [HttpPost("user/{userId}")]
        public async Task<IActionResult> CreateVehicle(Guid userId, [FromBody] CreateVehicleDto createVehicleDto)
        {
            try
            {
                var vehicle = await _vehicleService.CreateVehicleAsync(userId, createVehicleDto);
                return CreatedAtAction(nameof(GetVehicle), new { vehicleId = vehicle.Id }, vehicle);
            }
            catch (Exception ex)
            {
                return BadRequest(new { message = ex.Message });
            }
        }

        [HttpPut("{vehicleId}")]
        public async Task<IActionResult> UpdateVehicle(Guid vehicleId, [FromBody] CreateVehicleDto updateVehicleDto)
        {
            try
            {
                var vehicle = await _vehicleService.UpdateVehicleAsync(vehicleId, updateVehicleDto);
                return Ok(vehicle);
            }
            catch (Exception ex)
            {
                return BadRequest(new { message = ex.Message });
            }
        }

        [HttpDelete("{vehicleId}")]
        public async Task<IActionResult> DeleteVehicle(Guid vehicleId)
        {
            try
            {
                await _vehicleService.DeleteVehicleAsync(vehicleId);
                return NoContent();
            }
            catch (Exception ex)
            {
                return BadRequest(new { message = ex.Message });
            }
        }
    }
}