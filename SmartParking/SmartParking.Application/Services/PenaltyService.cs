using SmartParking.Application.DTOs;
using SmartParking.Application.Interfaces;
using SmartParking.Domain.Entities;
using SmartParking.Domain.Interfaces;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;

namespace SmartParking.Application.Services
{
    public class PenaltyService : IPenaltyService
    {
        private readonly IUnitOfWork _unitOfWork;

        public PenaltyService(IUnitOfWork unitOfWork)
        {
            _unitOfWork = unitOfWork;
        }

        // ========================================================
        // MEVCUT METODLAR (DEĞİŞMEDİ)
        // ========================================================

        public async Task<Penalty> IssuePenaltyAsync(Guid sessionId, string violationType, decimal amount, string description, string? imageUrl = null)
        {
            var penalty = new Penalty
            {
                ParkingSessionId = sessionId,
                ViolationType = violationType,
                Amount = amount,
                Description = description,
                ImageUrl = imageUrl,
                IssuedAt = DateTime.UtcNow,
                IsPaid = false
            };

            await _unitOfWork.Penalties.AddAsync(penalty);
            await _unitOfWork.SaveChangesAsync();

            return penalty;
        }

        public async Task<bool> PayPenaltyAsync(Guid penaltyId)
        {
            var penalty = await _unitOfWork.Penalties.GetByIdAsync(penaltyId);
            if (penalty == null || penalty.IsPaid)
                return false;

            penalty.IsPaid = true;
            penalty.PaidAt = DateTime.UtcNow;

            await _unitOfWork.Penalties.UpdateAsync(penalty);
            await _unitOfWork.SaveChangesAsync();

            return true;
        }

        public async Task<List<Penalty>> GetSessionPenaltiesAsync(Guid sessionId)
        {
            return await _unitOfWork.Penalties.GetBySessionIdAsync(sessionId);
        }

        public async Task<List<Penalty>> GetUnpaidPenaltiesAsync()
        {
            return await _unitOfWork.Penalties.GetUnpaidPenaltiesAsync();
        }

        public async Task<List<Penalty>> GetUserPenaltiesAsync(Guid userId)
        {
            return await _unitOfWork.Penalties.GetByUserIdAsync(userId);
        }

        // ========================================================
        // ✨ YENİ METODLAR - PYTHON DETECTION SİSTEMİ İÇİN
        // ========================================================

        /// <summary>
        /// Yol ihlali cezası kes (Python'dan gelen format)
        /// </summary>
        public async Task<Penalty> IssueRoadViolationAsync(RoadViolationDto dto)
        {
            Guid? vehicleId = null;

            // QR kod veya plaka ile Vehicle bulmaya çalış
            if (!string.IsNullOrEmpty(dto.QrCode) || !string.IsNullOrEmpty(dto.PlateNumber))
            {
                string searchValue = dto.QrCode ?? dto.PlateNumber;
                var allVehicles = await _unitOfWork.Vehicles.GetAllAsync();
                var vehicle = allVehicles.FirstOrDefault(v =>
                    v.PlateNumber == searchValue ||
                    v.PlateNumber == dto.QrCode ||
                    v.PlateNumber == dto.PlateNumber
                );
                vehicleId = vehicle?.Id;
            }

            var penalty = new Penalty
            {
                // Python'dan gelen yeni alanlar
                CameraName = dto.CameraName,
                DetectionVehicleId = dto.DetectionVehicleId,
                ZoneId = dto.ZoneId,

                // Mevcut sistem alanları
                ParkingSessionId = null,  // Yol ihlalinde session yok
                VehicleId = vehicleId,
                PlateNumber = dto.PlateNumber,
                QrCode = dto.QrCode,
                ViolationType = "road_violation",
                Amount = dto.Amount,
                Description = $"Yol ihlali - {dto.ZoneId} bölgesinde tespit edildi (Kamera: {dto.CameraName})",
                IssuedAt = dto.DetectionTime ?? DateTime.UtcNow,
                IsPaid = false,
                ImageUrl = dto.ImageUrl
            };

            await _unitOfWork.Penalties.AddAsync(penalty);
            await _unitOfWork.SaveChangesAsync();

            return penalty;
        }

        /// <summary>
        /// Yamuk park (birden fazla park yeri işgali) cezası kes (Python'dan gelen format)
        /// </summary>
        public async Task<Penalty> IssueMultiSpaceViolationAsync(MultiSpaceViolationDto dto)
        {
            Guid? vehicleId = null;

            // QR kod veya plaka ile Vehicle bulmaya çalış
            if (!string.IsNullOrEmpty(dto.QrCode) || !string.IsNullOrEmpty(dto.PlateNumber))
            {
                string searchValue = dto.QrCode ?? dto.PlateNumber;
                var allVehicles = await _unitOfWork.Vehicles.GetAllAsync();
                var vehicle = allVehicles.FirstOrDefault(v =>
                    v.PlateNumber == searchValue ||
                    v.PlateNumber == dto.QrCode ||
                    v.PlateNumber == dto.PlateNumber
                );
                vehicleId = vehicle?.Id;
            }

            // Park yerlerini JSON olarak kaydet
            var spacesJson = JsonSerializer.Serialize(dto.ParkingSpaceIds);

            var penalty = new Penalty
            {
                // Python'dan gelen yeni alanlar
                CameraName = dto.CameraName,
                DetectionVehicleId = dto.DetectionVehicleId,
                ParkingSpaceIds = spacesJson,  // JSON formatında

                // Mevcut sistem alanları
                ParkingSessionId = null,  // Yamuk park tespitinde session yok
                VehicleId = vehicleId,
                PlateNumber = dto.PlateNumber,
                QrCode = dto.QrCode,
                ViolationType = dto.ViolationType,
                Amount = dto.Amount,
                Description = $"Yamuk park - {dto.ParkingSpaceIds.Count} park yeri işgal edildi: {string.Join(", ", dto.ParkingSpaceIds)} (Kamera: {dto.CameraName})",
                IssuedAt = DateTime.UtcNow,
                IsPaid = false
            };

            await _unitOfWork.Penalties.AddAsync(penalty);
            await _unitOfWork.SaveChangesAsync();

            return penalty;
        }
    }
}
