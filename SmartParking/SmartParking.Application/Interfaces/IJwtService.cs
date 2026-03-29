using SmartParking.Domain.Entities;

namespace SmartParking.Application.Interfaces
{
    public interface IJwtService
    {
        string GenerateToken(User user);
    }
}