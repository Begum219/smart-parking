using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

using SmartParking.Domain.Entities;

namespace SmartParking.Domain.Interfaces
{
    public interface IPaymentRepository : IRepository<Payment>
    {
        Task<IEnumerable<Payment>> GetByUserIdAsync(Guid userId);
        Task<Payment?> GetBySessionIdAsync(Guid sessionId);
    }
}
