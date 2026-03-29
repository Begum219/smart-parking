using SmartParking.Application.DTOs;

namespace SmartParking.Application.Interfaces
{
    public interface IParkingService
    {
        Task<ParkingSessionDto> RecordDetectedVehicleAsync(DetectedVehicleDto detectionDto);
        Task<ParkingStatusDto> GetParkingStatusAsync();
        Task<IEnumerable<ParkingSpaceDto>> GetAvailableSpacesAsync();
        Task<ParkingSessionDto> StartParkingSessionAsync(Guid vehicleId, Guid parkingSpaceId);
        Task<ParkingSessionDto> EndParkingSessionAsync(Guid sessionId);
        Task<IEnumerable<ParkingSessionDto>> GetActiveSessionsAsync();
        Task<ParkingSessionDto?> GetActiveSessionByVehicleAsync(Guid vehicleId);
        /// <summary>
        /// Python'dan gelen park yerlerini sync et
        /// </summary>
        Task<int> SyncParkingSpacesAsync(ParkingSpaceSyncDto syncData);

        /// <summary>
        /// Tüm park yerlerini getir
        /// </summary>
        Task<List<ParkingSpaceDto>> GetAllParkingSpacesAsync();
        Task CloseSessionByDetectionVehicleIdAsync(int detectionVehicleId);
    }
}