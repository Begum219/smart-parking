using Microsoft.EntityFrameworkCore;
using SmartParking.Domain.Entities;
using SmartParking.Domain.Interfaces;
using SmartParking.Infrastructure.Data;

namespace SmartParking.Infrastructure.Repositories
{
    public class ParkingSpaceRepository : Repository<ParkingSpace>, IParkingSpaceRepository
    {
        public ParkingSpaceRepository(SmartParkingDbContext context) : base(context)
        {
        }

        public async Task<IEnumerable<ParkingSpace>> GetAvailableSpacesAsync()
        {
            return await _dbSet
                .Where(ps => !ps.IsOccupied && ps.Status == "available")
                .ToListAsync();
        }

        public async Task<ParkingSpace?> GetBySpaceNumberAsync(string spaceNumber)
        {
            return await _dbSet
                .FirstOrDefaultAsync(ps => ps.SpaceNumber == spaceNumber);
        }

        public async Task<int> GetOccupiedCountAsync()
        {
            return await _dbSet
                .CountAsync(ps => ps.IsOccupied);
        }
    }
}