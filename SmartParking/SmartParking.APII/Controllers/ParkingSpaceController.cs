using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartParking.Application.DTOs;
using SmartParking.Application.Interfaces;
using System;
using System.Threading.Tasks;

namespace SmartParking.API.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class ParkingSpaceController : ControllerBase
    {
        private readonly IParkingService _parkingService;

        public ParkingSpaceController(IParkingService parkingService)
        {
            _parkingService = parkingService;
        }

        /// <summary>
        /// Python'dan park yerlerini sync et
        /// </summary>
        [HttpPost("sync")]
        [AllowAnonymous]
        public async Task<IActionResult> SyncParkingSpaces([FromBody] ParkingSpaceSyncDto syncData)
        {
            try
            {
                if (syncData == null || syncData.ParkingSpaces == null || syncData.ParkingSpaces.Count == 0)
                {
                    return BadRequest(new { message = "Geçersiz veri" });
                }

                var count = await _parkingService.SyncParkingSpacesAsync(syncData);

                return Ok(new
                {
                    success = true,
                    message = $"{count} park yeri başarıyla sync edildi",
                    syncedCount = count,
                    cameraId = syncData.CameraId,
                    cameraName = syncData.CameraName
                });
            }
            catch (Exception ex)
            {
                return StatusCode(500, new { success = false, message = ex.Message });
            }
        }

        /// <summary>
        /// Tüm park yerlerini getir
        /// </summary>
        [HttpGet("all")]
        [Authorize]
        public async Task<IActionResult> GetAllParkingSpaces()
        {
            try
            {
                var spaces = await _parkingService.GetAllParkingSpacesAsync();
                return Ok(spaces);
            }
            catch (Exception ex)
            {
                return StatusCode(500, new { message = ex.Message });
            }
        }

        /// <summary>
        /// Boş park yerlerini getir
        /// </summary>
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
                return StatusCode(500, new { message = ex.Message });
            }
        }

        /// <summary>
        /// Park yeri durumunu manuel güncelle
        /// </summary>
        [HttpPut("{spaceNumber}/toggle")]
        [Authorize(Roles = "Admin")]
        public IActionResult ToggleSpaceStatus(string spaceNumber)  // ✅ async kaldırıldı
        {
            // TODO: Implement edildiğinde async Task<IActionResult> yapılacak
            return Ok(new { message = "Not implemented yet" });
        }
    }
}