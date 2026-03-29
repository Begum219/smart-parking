using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartParking.Application.Interfaces;
using System;
using System.Security.Claims;
using System.Threading.Tasks;
using SmartParking.Application.DTOs;

namespace SmartParking.API.Controllers
{
    [Authorize]
    [ApiController]
    [Route("api/[controller]")]
    public class PenaltyController : ControllerBase
    {
        private readonly IPenaltyService _penaltyService;

        public PenaltyController(IPenaltyService penaltyService)
        {
            _penaltyService = penaltyService;
        }

        // ========================================================
        // MEVCUT METODLAR (DEĞİŞMEDİ)
        // ========================================================

        // POST: api/Penalty/issue
        [HttpPost("issue")]
        public async Task<IActionResult> IssuePenalty([FromBody] PenaltyDto dto)
        {
            try
            {
                var penalty = await _penaltyService.IssuePenaltyAsync(
                    dto.SessionId,
                    dto.ViolationType,
                    dto.Amount,
                    dto.Description,
                    dto.ImageUrl
                );

                return Ok(new
                {
                    message = "Ceza başarıyla kesildi",
                    penalty
                });
            }
            catch (Exception ex)
            {
                return BadRequest(new { message = ex.Message });
            }
        }

        // POST: api/Penalty/pay/{penaltyId}
        [HttpPost("pay/{penaltyId}")]
        public async Task<IActionResult> PayPenalty(Guid penaltyId)
        {
            try
            {
                var success = await _penaltyService.PayPenaltyAsync(penaltyId);

                if (!success)
                    return NotFound(new { message = "Ceza bulunamadı veya zaten ödendi" });

                return Ok(new { message = "Ceza başarıyla ödendi" });
            }
            catch (Exception ex)
            {
                return BadRequest(new { message = ex.Message });
            }
        }

        // GET: api/Penalty/my-penalties
        [HttpGet("my-penalties")]
        public async Task<IActionResult> GetMyPenalties()
        {
            try
            {
                var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
                if (string.IsNullOrEmpty(userIdClaim))
                    return Unauthorized(new { message = "Kullanıcı bulunamadı" });

                var userId = Guid.Parse(userIdClaim);
                var penalties = await _penaltyService.GetUserPenaltiesAsync(userId);

                return Ok(penalties);
            }
            catch (Exception ex)
            {
                return BadRequest(new { message = ex.Message });
            }
        }

        // GET: api/Penalty/unpaid (Admin only)
        [HttpGet("unpaid")]
        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> GetUnpaidPenalties()
        {
            try
            {
                var penalties = await _penaltyService.GetUnpaidPenaltiesAsync();
                return Ok(penalties);
            }
            catch (Exception ex)
            {
                return BadRequest(new { message = ex.Message });
            }
        }

        // GET: api/Penalty/session/{sessionId}
        [HttpGet("session/{sessionId}")]
        public async Task<IActionResult> GetSessionPenalties(Guid sessionId)
        {
            try
            {
                var penalties = await _penaltyService.GetSessionPenaltiesAsync(sessionId);
                return Ok(penalties);
            }
            catch (Exception ex)
            {
                return BadRequest(new { message = ex.Message });
            }
        }

        // ========================================================
        // ✨ PYTHON DETECTION SİSTEMİ İÇİN YENİ ENDPOINT'LER
        // ========================================================

        /// <summary>
        /// Yol ihlali (şerit ihlali) cezası kes
        /// Python detection sistemi tarafından çağrılır
        /// </summary>
        [HttpPost("issue-road-violation")]
        [AllowAnonymous]
        public async Task<IActionResult> IssueRoadViolation([FromBody] RoadViolationDto dto)
        {
            try
            {
                if (dto == null)
                    return BadRequest(new { message = "Veri boş olamaz" });

                var penalty = await _penaltyService.IssueRoadViolationAsync(dto);

                return Ok(new
                {
                    success = true,
                    message = "Yol ihlali cezası başarıyla kesildi",
                    penalty = new
                    {
                        penalty.Id,
                        penalty.ViolationType,
                        penalty.Amount,
                        penalty.IssuedAt,
                        penalty.PlateNumber,
                        penalty.QrCode,
                        penalty.ZoneId,
                        penalty.CameraName,
                        penalty.Description
                    }
                });
            }
            catch (Exception ex)
            {
                return StatusCode(500, new { success = false, message = ex.Message });
            }
        }

        /// <summary>
        /// Yamuk park (birden fazla park yeri işgali) cezası kes
        /// Python detection sistemi tarafından çağrılır
        /// </summary>
        [HttpPost("issue-multi-space-violation")]
        [AllowAnonymous]
        public async Task<IActionResult> IssueMultiSpaceViolation([FromBody] MultiSpaceViolationDto dto)
        {
            try
            {
                if (dto == null)
                    return BadRequest(new { message = "Veri boş olamaz" });

                if (dto.ParkingSpaceIds == null || dto.ParkingSpaceIds.Count < 2)
                    return BadRequest(new { message = "En az 2 park yeri işgali gerekli" });

                var penalty = await _penaltyService.IssueMultiSpaceViolationAsync(dto);

                return Ok(new
                {
                    success = true,
                    message = $"Yamuk park cezası başarıyla kesildi ({dto.ParkingSpaceIds.Count} park yeri işgal edildi)",
                    penalty = new
                    {
                        penalty.Id,
                        penalty.ViolationType,
                        penalty.Amount,
                        penalty.IssuedAt,
                        penalty.PlateNumber,
                        penalty.QrCode,
                        ParkingSpaces = dto.ParkingSpaceIds,
                        penalty.CameraName,
                        penalty.Description
                    }
                });
            }
            catch (Exception ex)
            {
                return StatusCode(500, new { success = false, message = ex.Message });
            }
        }
    }
}