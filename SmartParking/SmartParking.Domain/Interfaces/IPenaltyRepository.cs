using SmartParking.Domain.Entities;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace SmartParking.Domain.Interfaces
{
    public interface IPenaltyRepository : IRepository<Penalty>
    {
        Task<List<Penalty>> GetBySessionIdAsync(Guid sessionId);
        Task<List<Penalty>> GetUnpaidPenaltiesAsync();
        Task<List<Penalty>> GetByUserIdAsync(Guid userId);

        // ✅ YENİ METODLAR - Plaka/QR ile sorgulama
        Task<List<Penalty>> GetByPlateNumberAsync(string plateNumber);
        Task<List<Penalty>> GetByQrCodeAsync(string qrCode);
        Task<List<Penalty>> GetByVehicleIdAsync(Guid vehicleId);
    }
}