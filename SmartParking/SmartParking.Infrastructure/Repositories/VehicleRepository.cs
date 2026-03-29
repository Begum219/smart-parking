using Microsoft.EntityFrameworkCore;
using SmartParking.Domain.Entities;
using SmartParking.Domain.Interfaces;
using SmartParking.Infrastructure.Data;

namespace SmartParking.Infrastructure.Repositories
{
    public class VehicleRepository : Repository<Vehicle>, IVehicleRepository
    {
        public VehicleRepository(SmartParkingDbContext context) : base(context)
        {
        }

        public async Task<IEnumerable<Vehicle>> GetByUserIdAsync(Guid userId)
        {
            return await _dbSet
                .Where(v => v.UserId == userId && v.IsActive)
                .ToListAsync();
        }

        public async Task<Vehicle?> GetByLabelAsync(string label)
        {
            return await _dbSet
                .FirstOrDefaultAsync(v => v.Label == label);
        }
    }
}