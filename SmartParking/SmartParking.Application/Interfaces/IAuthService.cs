using SmartParking.Application.DTOs;
using SmartParking.Application.DTOs.Auth;

namespace SmartParking.Application.Interfaces
{
    public interface IAuthService
    {
        Task<AuthResponseDto> RegisterAsync(RegisterDto registerDto);
        Task<AuthResponseDto> LoginAsync(LoginDto loginDto);
        Task<UserDto> GetUserByIdAsync(Guid userId);
        Task<UserDto> UpdateProfileAsync(Guid userId, UpdateProfileDto updateProfileDto);
        Task ChangePasswordAsync(Guid userId, ChangePasswordDto changePasswordDto);
    }
}