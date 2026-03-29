using SmartParking.Application.DTOs;

namespace SmartParking.Application.Interfaces
{
    public interface IVehicleService
    {
        Task<IEnumerable<VehicleDto>> GetUserVehiclesAsync(Guid userId);
        Task<VehicleDto> GetVehicleByIdAsync(Guid vehicleId);
        Task<VehicleDto> CreateVehicleAsync(Guid userId, CreateVehicleDto createVehicleDto);
        Task<VehicleDto> UpdateVehicleAsync(Guid vehicleId, CreateVehicleDto updateVehicleDto);
        Task DeleteVehicleAsync(Guid vehicleId);
    }
}