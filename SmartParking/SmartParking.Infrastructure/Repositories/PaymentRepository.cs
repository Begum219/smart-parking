using Microsoft.EntityFrameworkCore;
using SmartParking.Domain.Entities;
using SmartParking.Domain.Interfaces;
using SmartParking.Infrastructure.Data;

namespace SmartParking.Infrastructure.Repositories
{
    public class PaymentRepository : Repository<Payment>, IPaymentRepository
    {
        public PaymentRepository(SmartParkingDbContext context) : base(context)
        {
        }

        public async Task<IEnumerable<Payment>> GetByUserIdAsync(Guid userId)
        {
            return await _dbSet
                .Include(p => p.Session)
                .Where(p => p.UserId == userId)
                .OrderByDescending(p => p.PaymentTime)
                .ToListAsync();
        }

        public async Task<Payment?> GetBySessionIdAsync(Guid sessionId)
        {
            return await _dbSet
                .FirstOrDefaultAsync(p => p.SessionId == sessionId);
        }
    }
}