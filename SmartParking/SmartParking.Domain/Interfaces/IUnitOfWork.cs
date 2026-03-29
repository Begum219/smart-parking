using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SmartParking.Domain.Interfaces
{
    public interface IUnitOfWork : IDisposable
    {
        IUserRepository Users { get; }
        IVehicleRepository Vehicles { get; }
        IParkingSpaceRepository ParkingSpaces { get; }
        IParkingSessionRepository ParkingSessions { get; }
        IPaymentRepository Payments { get; }
        IPenaltyRepository Penalties { get; }
        Task<int> SaveChangesAsync();
    }
}