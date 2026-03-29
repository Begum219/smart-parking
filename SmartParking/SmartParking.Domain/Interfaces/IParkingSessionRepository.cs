using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

using SmartParking.Domain.Entities;

namespace SmartParking.Domain.Interfaces
{
    public interface IParkingSessionRepository : IRepository<ParkingSession>
    {
        Task<IEnumerable<ParkingSession>> GetActiveSessionsAsync();
        Task<ParkingSession?> GetActiveSessionByVehicleIdAsync(Guid vehicleId);
        Task<IEnumerable<ParkingSession>> GetSessionsByDateRangeAsync(DateTime startDate, DateTime endDate);
    }
}