using SmartParking.Domain.Interfaces;
using SmartParking.Infrastructure.Data;

namespace SmartParking.Infrastructure.Repositories
{
    public class UnitOfWork : IUnitOfWork
    {
        private readonly SmartParkingDbContext _context;

        public IUserRepository Users { get; private set; }
        public IVehicleRepository Vehicles { get; private set; }
        public IParkingSpaceRepository ParkingSpaces { get; private set; }
        public IParkingSessionRepository ParkingSessions { get; private set; }
        public IPaymentRepository Payments { get; private set; }
        public IPenaltyRepository Penalties { get; private set; }

        public UnitOfWork(SmartParkingDbContext context)
        {
            _context = context;

            Users = new UserRepository(_context);
            Vehicles = new VehicleRepository(_context);
            ParkingSpaces = new ParkingSpaceRepository(_context);
            ParkingSessions = new ParkingSessionRepository(_context);
            Payments = new PaymentRepository(_context);
            Penalties = new PenaltyRepository(_context);
        }

        public async Task<int> SaveChangesAsync()
        {
            return await _context.SaveChangesAsync();
        }

        public void Dispose()
        {
            _context.Dispose();
        }
    }
}