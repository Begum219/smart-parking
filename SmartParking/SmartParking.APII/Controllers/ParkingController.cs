using Microsoft.AspNetCore.Mvc;
using SmartParking.Application.DTOs;
using SmartParking.Application.Interfaces;

namespace SmartParking.API.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class ParkingController : ControllerBase
    {
        private readonly IParkingService _parkingService;

        public ParkingController(IParkingService parkingService)
        {
            _parkingService = parkingService;
        }

        [HttpGet("status")]
        public async Task<IActionResult> GetParkingStatus()
        {
            try
            {
                var status = await _parkingService.GetParkingStatusAsync();
                return Ok(status);
            }
            catch (Exception ex)
            {
                return BadRequest(new { message = ex.Message });
            }
        }

        [HttpGet("available")]
        public async Task<IActionResult> GetAvailableSpaces()
        {
            try
            {
                var spaces = await _parkingService.GetAvailableSpacesAsync();
                return Ok(spaces);
            }
            catch (Exception ex)
            {
                return BadRequest(new { message = ex.Message });
            }
        }

        [HttpPost("start")]
        public async Task<IActionResult> StartParking([FromQuery] Guid vehicleId, [FromQuery] Guid parkingSpaceId)
        {
            try
            {
                var session = await _parkingService.StartParkingSessionAsync(vehicleId, parkingSpaceId);
                return Ok(session);
            }
            catch (Exception ex)
            {
                return BadRequest(new { message = ex.Message });
            }
        }

        [HttpPost("end/{sessionId}")]
        public async Task<IActionResult> EndParking(Guid sessionId)
        {
            try
            {
                var session = await _parkingService.EndParkingSessionAsync(sessionId);
                return Ok(session);
            }
            catch (Exception ex)
            {
                return BadRequest(new { message = ex.Message });
            }
        }

        [HttpGet("active-sessions")]
        public async Task<IActionResult> GetActiveSessions()
        {
            try
            {
                var sessions = await _parkingService.GetActiveSessionsAsync();
                return Ok(sessions);
            }
            catch (Exception ex)
            {
                return BadRequest(new { message = ex.Message });
            }
        }

        [HttpGet("vehicle/{vehicleId}/active-session")]
        public async Task<IActionResult> GetActiveSessionByVehicle(Guid vehicleId)
        {
            try
            {
                var session = await _parkingService.GetActiveSessionByVehicleAsync(vehicleId);
                if (session == null)
                {
                    return NotFound(new { message = "No active session found for this vehicle" });
                }
                return Ok(session);
            }
            catch (Exception ex)
            {
                return BadRequest(new { message = ex.Message });
            }
        }
        [HttpPost("detect")]
        public async Task<IActionResult> DetectVehicle([FromBody] DetectedVehicleDto detectionDto)
        {
            try
            {
                if (detectionDto == null)
                    return BadRequest(new { error = "Araç tespit verisi boş olamaz" });

                var parkingSession = await _parkingService.RecordDetectedVehicleAsync(detectionDto);

                return Ok(new
                {
                    success = true,
                    message = $"Araç {detectionDto.VehicleId} kaydedildi",
                    sessionId = parkingSession.Id,
                    vehicleId = detectionDto.VehicleId,
                    confidence = detectionDto.Confidence
                });
            }
            catch (Exception ex)
            {
                return BadRequest(new { error = ex.Message });
            }
        }
        [HttpPost("vehicle-left/{detectionVehicleId}")]
        public async Task<IActionResult> VehicleLeft(int detectionVehicleId)
        {
            try
            {
                await _parkingService.CloseSessionByDetectionVehicleIdAsync(detectionVehicleId);
                return Ok(new { success = true, message = $"Araç {detectionVehicleId} ayrıldı" });
            }
            catch (Exception ex)
            {
                return BadRequest(new { error = ex.Message });
            }
        }
    }
}