using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartParking.Application.DTOs;
using SmartParking.Application.Interfaces;
using SmartParking.Domain.Enums;
using SmartParking.Domain.Interfaces;

namespace SmartParking.API.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class UserController : ControllerBase
    {
        private readonly IAuthService _authService;
        private readonly IUnitOfWork _unitOfWork;

        public UserController(IAuthService authService, IUnitOfWork unitOfWork)
        {
            _authService = authService;
            _unitOfWork = unitOfWork;
        }

        // ========== MEVCUT ENDPOINT'LER ==========

        [HttpPut("{userId}")]
        public async Task<IActionResult> UpdateProfile(Guid userId, [FromBody] UpdateProfileDto updateProfileDto)
        {
            try
            {
                var user = await _authService.UpdateProfileAsync(userId, updateProfileDto);
                return Ok(user);
            }
            catch (Exception ex)
            {
                return BadRequest(new { message = ex.Message });
            }
        }

        [HttpPost("{userId}/change-password")]
        public async Task<IActionResult> ChangePassword(Guid userId, [FromBody] ChangePasswordDto changePasswordDto)
        {
            try
            {
                await _authService.ChangePasswordAsync(userId, changePasswordDto);
                return Ok(new { message = "Password changed successfully" });
            }
            catch (Exception ex)
            {
                return BadRequest(new { message = ex.Message });
            }
        }

        // ========== YENİ ADMIN ENDPOINT'LERİ ==========

        // Tüm kullanıcıları listele (Sadece Admin/Manager)
        [HttpGet]
        [Authorize(Roles = "Admin,Manager")]
        public async Task<IActionResult> GetAllUsers()
        {
            try
            {
                var users = await _unitOfWork.Users.GetAllAsync();
                return Ok(users);
            }
            catch (Exception ex)
            {
                return BadRequest(new { message = ex.Message });
            }
        }

        // Kullanıcıyı aktif/pasif yap (Sadece Admin)
        [HttpPatch("{userId}/toggle-active")]
        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> ToggleUserActive(Guid userId)
        {
            try
            {
                var user = await _unitOfWork.Users.GetByIdAsync(userId);
                if (user == null)
                    return NotFound(new { message = "User not found" });

                user.IsActive = !user.IsActive;
                user.UpdatedAt = DateTime.UtcNow;
                await _unitOfWork.SaveChangesAsync();

                return Ok(new { message = "User status updated", isActive = user.IsActive });
            }
            catch (Exception ex)
            {
                return BadRequest(new { message = ex.Message });
            }
        }

        // Kullanıcı rolünü güncelle (Sadece Admin)
        [HttpPatch("{userId}/update-role")]
        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> UpdateUserRole(Guid userId, [FromBody] UpdateRoleRequest request)
        {
            try
            {
                var user = await _unitOfWork.Users.GetByIdAsync(userId);
                if (user == null)
                    return NotFound(new { message = "User not found" });

                // String'i enum'a çevir
                if (Enum.TryParse<UserRole>(request.Role, out var userRole))
                {
                    user.Role = userRole;
                    user.UpdatedAt = DateTime.UtcNow;
                    await _unitOfWork.SaveChangesAsync();
                    return Ok(new { message = "User role updated" });
                }
                else
                {
                    return BadRequest(new { message = "Invalid role" });
                }
            }
            catch (Exception ex)
            {
                return BadRequest(new { message = ex.Message });
            }
        }

        // Kullanıcıyı sil (Sadece Admin)
        [HttpDelete("{userId}")]
        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> DeleteUser(Guid userId)
        {
            try
            {
                var user = await _unitOfWork.Users.GetByIdAsync(userId);
                if (user == null)
                    return NotFound(new { message = "User not found" });

                await _unitOfWork.Users.DeleteAsync(userId); // ✅ Sadece ID gönder
                await _unitOfWork.SaveChangesAsync();

                return Ok(new { message = "User deleted successfully" });
            }
            catch (Exception ex)
            {
                return BadRequest(new { message = ex.Message });
            }
        }
    }

    // Request DTO
    public class UpdateRoleRequest
    {
        public string Role { get; set; } = string.Empty;
    }
}