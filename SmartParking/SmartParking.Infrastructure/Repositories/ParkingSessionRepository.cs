using Microsoft.EntityFrameworkCore;
using SmartParking.Domain.Entities;
using SmartParking.Domain.Interfaces;
using SmartParking.Infrastructure.Data;

namespace SmartParking.Infrastructure.Repositories
{
    public class ParkingSessionRepository : Repository<ParkingSession>, IParkingSessionRepository
    {
        public ParkingSessionRepository(SmartParkingDbContext context) : base(context)
        {
        }

        public async Task<IEnumerable<ParkingSession>> GetActiveSessionsAsync()
        {
            return await _dbSet
                .Include(ps => ps.Vehicle)
                .Include(ps => ps.ParkingSpace)
                .Where(ps => ps.SessionStatus == "active")
                .ToListAsync();
        }

        public async Task<ParkingSession?> GetActiveSessionByVehicleIdAsync(Guid vehicleId)
        {
            return await _dbSet
                .Include(ps => ps.ParkingSpace)
                .FirstOrDefaultAsync(ps => ps.VehicleId == vehicleId && ps.SessionStatus == "active");
        }

        public async Task<IEnumerable<ParkingSession>> GetSessionsByDateRangeAsync(DateTime startDate, DateTime endDate)
        {
            return await _dbSet
                .Include(ps => ps.Vehicle)
                .Include(ps => ps.ParkingSpace)
                .Where(ps => ps.EntryTime >= startDate && ps.EntryTime <= endDate)
                .ToListAsync();
        }
    }
}