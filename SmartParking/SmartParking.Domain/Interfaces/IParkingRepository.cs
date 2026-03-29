using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

using SmartParking.Domain.Entities;

namespace SmartParking.Domain.Interfaces
{
    public interface IParkingSpaceRepository : IRepository<ParkingSpace>
    {
        Task<IEnumerable<ParkingSpace>> GetAvailableSpacesAsync();
        Task<ParkingSpace?> GetBySpaceNumberAsync(string spaceNumber);
        Task<int> GetOccupiedCountAsync();
    }
}