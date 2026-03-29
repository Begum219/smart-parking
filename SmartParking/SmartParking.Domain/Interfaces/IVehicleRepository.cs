using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

using SmartParking.Domain.Entities;

namespace SmartParking.Domain.Interfaces
{
    public interface IVehicleRepository : IRepository<Vehicle>
    {
        Task<IEnumerable<Vehicle>> GetByUserIdAsync(Guid userId);
        Task<Vehicle?> GetByLabelAsync(string label);
    }
}