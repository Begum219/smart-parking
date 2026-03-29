using Microsoft.EntityFrameworkCore;
using SmartParking.Domain.Entities;
using SmartParking.Domain.Interfaces;
using SmartParking.Infrastructure.Data;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace SmartParking.Infrastructure.Repositories
{
    public class PenaltyRepository : Repository<Penalty>, IPenaltyRepository
    {
        public PenaltyRepository(SmartParkingDbContext context) : base(context)
        {
        }

        public async Task<List<Penalty>> GetBySessionIdAsync(Guid sessionId)
        {
            return await _context.Penalties
                .Where(p => p.ParkingSessionId == sessionId)
                .Include(p => p.ParkingSession)
                .Include(p => p.Vehicle)  // ✅ YENİ
                .OrderByDescending(p => p.IssuedAt)
                .ToListAsync();
        }

        public async Task<List<Penalty>> GetUnpaidPenaltiesAsync()
        {
            return await _context.Penalties
                .Where(p => !p.IsPaid)
                .Include(p => p.ParkingSession)
                    .ThenInclude(ps => ps!.Vehicle)
                .Include(p => p.Vehicle)  // ✅ YENİ
                .OrderByDescending(p => p.IssuedAt)
                .ToListAsync();
        }

        public async Task<List<Penalty>> GetByUserIdAsync(Guid userId)
        {
            return await _context.Penalties
                .Include(p => p.ParkingSession)
                    .ThenInclude(ps => ps!.Vehicle)
                .Include(p => p.Vehicle)  // ✅ YENİ
                .Where(p =>
                    // Session üzerinden
                    (p.ParkingSession != null &&
                     p.ParkingSession.Vehicle != null &&
                     p.ParkingSession.Vehicle.UserId == userId)
                    ||
                    // ✅ YENİ: Direkt Vehicle üzerinden
                    (p.Vehicle != null && p.Vehicle.UserId == userId)
                )
                .OrderByDescending(p => p.IssuedAt)
                .ToListAsync();
        }

        // ✅ YENİ METODLAR

        public async Task<List<Penalty>> GetByPlateNumberAsync(string plateNumber)
        {
            return await _context.Penalties
                .Where(p => p.PlateNumber == plateNumber)
                .Include(p => p.ParkingSession)
                .Include(p => p.Vehicle)
                .OrderByDescending(p => p.IssuedAt)
                .ToListAsync();
        }

        public async Task<List<Penalty>> GetByQrCodeAsync(string qrCode)
        {
            return await _context.Penalties
                .Where(p => p.QrCode == qrCode)
                .Include(p => p.ParkingSession)
                .Include(p => p.Vehicle)
                .OrderByDescending(p => p.IssuedAt)
                .ToListAsync();
        }

        public async Task<List<Penalty>> GetByVehicleIdAsync(Guid vehicleId)
        {
            return await _context.Penalties
                .Include(p => p.ParkingSession)
                .Include(p => p.Vehicle)
                .Where(p =>
                    p.VehicleId == vehicleId ||
                    (p.ParkingSession != null && p.ParkingSession.VehicleId == vehicleId)
                )
                .OrderByDescending(p => p.IssuedAt)
                .ToListAsync();
        }
    }
}