using AutoMapper;
using SmartParking.Application.DTOs;
using SmartParking.Application.Interfaces;
using SmartParking.Domain.Entities;
using SmartParking.Domain.Interfaces;
using System.Text.Json;

namespace SmartParking.Application.Services
{
    public class ParkingService : IParkingService
    {
        private readonly IUnitOfWork _unitOfWork;
        private readonly IMapper _mapper;

        // ✅ ESKİ HALİYLE - IPricingService YOK!
        public ParkingService(IUnitOfWork unitOfWork, IMapper mapper)
        {
            _unitOfWork = unitOfWork;
            _mapper = mapper;
        }

        public async Task<ParkingStatusDto> GetParkingStatusAsync()
        {
            var allSpaces = await _unitOfWork.ParkingSpaces.GetAllAsync();
            var occupiedCount = await _unitOfWork.ParkingSpaces.GetOccupiedCountAsync();
            var totalCount = allSpaces.Count();
            var availableCount = totalCount - occupiedCount;

            return new ParkingStatusDto
            {
                TotalSpaces = totalCount,
                OccupiedSpaces = occupiedCount,
                AvailableSpaces = availableCount,
                OccupancyRate = totalCount > 0 ? (double)occupiedCount / totalCount * 100 : 0,
                Spaces = _mapper.Map<List<ParkingSpaceDto>>(allSpaces)
            };
        }

        public async Task<IEnumerable<ParkingSpaceDto>> GetAvailableSpacesAsync()
        {
            var availableSpaces = await _unitOfWork.ParkingSpaces.GetAvailableSpacesAsync();
            return _mapper.Map<IEnumerable<ParkingSpaceDto>>(availableSpaces);
        }

        public async Task<ParkingSessionDto> StartParkingSessionAsync(Guid vehicleId, Guid parkingSpaceId)
        {
            // Araç kontrolü
            var vehicle = await _unitOfWork.Vehicles.GetByIdAsync(vehicleId);
            if (vehicle == null)
            {
                throw new Exception("Vehicle not found");
            }

            // Park yeri kontrolü
            var parkingSpace = await _unitOfWork.ParkingSpaces.GetByIdAsync(parkingSpaceId);
            if (parkingSpace == null)
            {
                throw new Exception("Parking space not found");
            }

            if (parkingSpace.IsOccupied)
            {
                throw new Exception("Parking space is already occupied");
            }

            // Aktif oturum kontrolü
            var activeSession = await _unitOfWork.ParkingSessions.GetActiveSessionByVehicleIdAsync(vehicleId);
            if (activeSession != null)
            {
                throw new Exception("Vehicle already has an active parking session");
            }

            // Yeni oturum oluştur
            var session = new ParkingSession
            {
                VehicleId = vehicleId,
                ParkingSpaceId = parkingSpaceId,
                EntryTime = DateTime.UtcNow,
                SessionStatus = "active",
                PaymentStatus = "pending"
            };

            await _unitOfWork.ParkingSessions.AddAsync(session);

            // Park yerini güncelle
            parkingSpace.IsOccupied = true;
            parkingSpace.Status = "occupied";
            await _unitOfWork.ParkingSpaces.UpdateAsync(parkingSpace);

            await _unitOfWork.SaveChangesAsync();

            // DTO'ya çevir
            session.Vehicle = vehicle;
            session.ParkingSpace = parkingSpace;
            return _mapper.Map<ParkingSessionDto>(session);
        }

        public async Task<ParkingSessionDto> RecordDetectedVehicleAsync(DetectedVehicleDto detectionDto)
        {
            if (detectionDto == null)
                throw new Exception("Detection verisi boş");

            if (detectionDto.Confidence < 0.001)
                throw new Exception($"Confidence çok düşük: {detectionDto.Confidence:F2}");

            // Plakaya göre kayıtlı araç ara
            Guid? matchedVehicleId = null;
            if (!string.IsNullOrEmpty(detectionDto.PlateNumber))
            {
                var allVehicles = await _unitOfWork.Vehicles.GetAllAsync();
                var matchedVehicle = allVehicles.FirstOrDefault(v =>
                    v.PlateNumber != null &&
                    v.PlateNumber.Replace(" ", "").ToUpper() ==
                    detectionDto.PlateNumber.Replace(" ", "").ToUpper());

                if (matchedVehicle != null)
                    matchedVehicleId = matchedVehicle.Id;
            }

            // Aktif session var mı?
            var allActive = await _unitOfWork.ParkingSessions.GetActiveSessionsAsync();
            var existingSession = allActive.FirstOrDefault(s =>
                s.DetectionVehicleId == detectionDto.VehicleId &&
                s.SessionStatus == "active");

            if (existingSession != null)
            {
                existingSession.Confidence = detectionDto.Confidence;
                existingSession.UpdatedAt = DateTime.UtcNow;

                if (!string.IsNullOrEmpty(detectionDto.QrCode))
                    existingSession.QrCode = detectionDto.QrCode;
                if (!string.IsNullOrEmpty(detectionDto.PlateNumber))
                    existingSession.DetectedPlateNumber = detectionDto.PlateNumber;

                // VehicleId hâlâ null ise eşleştir
                if (existingSession.VehicleId == null && matchedVehicleId != null)
                    existingSession.VehicleId = matchedVehicleId;

                if (!string.IsNullOrEmpty(detectionDto.ParkingSpaceName))
                {
                    var allSpaces = await _unitOfWork.ParkingSpaces.GetAllAsync();
                    var space = allSpaces.FirstOrDefault(p =>
                        p.SpaceNumber == detectionDto.ParkingSpaceName);
                    if (space != null)
                    {
                        existingSession.ParkingSpaceId = space.Id;
                        space.IsOccupied = true;
                        space.Status = "occupied";
                        await _unitOfWork.ParkingSpaces.UpdateAsync(space);
                    }
                }

                await _unitOfWork.ParkingSessions.UpdateAsync(existingSession);
                await _unitOfWork.SaveChangesAsync();

                return new ParkingSessionDto
                {
                    Id = existingSession.Id,
                    EntryTime = existingSession.EntryTime,
                    SessionStatus = existingSession.SessionStatus,
                    DetectionVehicleId = existingSession.DetectionVehicleId,
                    DetectedPlateNumber = existingSession.DetectedPlateNumber,
                    QrCode = existingSession.QrCode,
                    Confidence = existingSession.Confidence
                };
            }

            // Yeni session aç
            ParkingSpace? parkingSpace = null;
            if (!string.IsNullOrEmpty(detectionDto.ParkingSpaceName))
            {
                var allSpaces = await _unitOfWork.ParkingSpaces.GetAllAsync();
                parkingSpace = allSpaces.FirstOrDefault(p =>
                    p.SpaceNumber == detectionDto.ParkingSpaceName);
                if (parkingSpace != null)
                {
                    parkingSpace.IsOccupied = true;
                    parkingSpace.Status = "occupied";
                    await _unitOfWork.ParkingSpaces.UpdateAsync(parkingSpace);
                }
            }

            var session = new ParkingSession
            {
                VehicleId = matchedVehicleId,  // ← Plaka eşleşti ise dolu, yoksa null
                ParkingSpaceId = parkingSpace?.Id,
                EntryTime = DateTime.UtcNow,
                SessionStatus = "active",
                PaymentStatus = "pending",
                DetectionVehicleId = detectionDto.VehicleId,
                DetectedPlateNumber = detectionDto.PlateNumber,
                QrCode = detectionDto.QrCode,
                Confidence = detectionDto.Confidence
            };

            await _unitOfWork.ParkingSessions.AddAsync(session);
            await _unitOfWork.SaveChangesAsync();

            return new ParkingSessionDto
            {
                Id = session.Id,
                EntryTime = session.EntryTime,
                SessionStatus = session.SessionStatus,
                DetectionVehicleId = session.DetectionVehicleId,
                DetectedPlateNumber = session.DetectedPlateNumber,
                Confidence = session.Confidence
            };
        }
        public async Task CloseSessionByDetectionVehicleIdAsync(int detectionVehicleId)
        {
            var allActive = await _unitOfWork.ParkingSessions.GetActiveSessionsAsync();
            var session = allActive.FirstOrDefault(s =>
                s.DetectionVehicleId == detectionVehicleId &&
                s.SessionStatus == "active");

            if (session == null) return;

            session.ExitTime = DateTime.UtcNow;
            session.DurationMinutes = (int)Math.Ceiling((session.ExitTime.Value - session.EntryTime).TotalMinutes);
            session.SessionStatus = "completed";
            session.TotalFee = CalculateParkingFee(session.DurationMinutes.Value);

            await _unitOfWork.ParkingSessions.UpdateAsync(session);

            if (session.ParkingSpaceId.HasValue)
            {
                var space = await _unitOfWork.ParkingSpaces.GetByIdAsync(session.ParkingSpaceId.Value);
                if (space != null)
                {
                    space.IsOccupied = false;
                    space.Status = "available";
                    await _unitOfWork.ParkingSpaces.UpdateAsync(space);
                }
            }

            await _unitOfWork.SaveChangesAsync();
        }

        /// <summary>
        /// ✅ SADECE PaymentStatus SATIRI KALDIRILDI
        /// ✅ ESKİ CalculateParkingFee METODU KORUNDU
        /// </summary>
        public async Task<ParkingSessionDto> EndParkingSessionAsync(Guid sessionId)
        {
            var session = await _unitOfWork.ParkingSessions.GetByIdAsync(sessionId);
            if (session == null)
            {
                throw new Exception("Parking session not found");
            }

            if (session.SessionStatus != "active")
            {
                throw new Exception("Session is not active");
            }

            // Çıkış zamanını kaydet
            session.ExitTime = DateTime.UtcNow;
            session.DurationMinutes = (int)(session.ExitTime.Value - session.EntryTime).TotalMinutes;
            session.SessionStatus = "completed";

            // ✅ ESKİ HESAPLAMA KORUNDU
            session.TotalFee = CalculateParkingFee(session.DurationMinutes.Value);

            // ❌ TEK DEĞİŞİKLİK: PaymentStatus satırı kaldırıldı
            // ESKİ: session.PaymentStatus = "paid";
            // ŞİMDİ: PaymentController bu durumu güncelleyecek

            await _unitOfWork.ParkingSessions.UpdateAsync(session);

            // Park yerini boşalt
            if (session.ParkingSpaceId.HasValue)
            {
                var parkingSpace = await _unitOfWork.ParkingSpaces.GetByIdAsync(session.ParkingSpaceId.Value);
                if (parkingSpace != null)
                {
                    parkingSpace.IsOccupied = false;
                    parkingSpace.Status = "available";
                    await _unitOfWork.ParkingSpaces.UpdateAsync(parkingSpace);
                }
            }

            await _unitOfWork.SaveChangesAsync();

            return _mapper.Map<ParkingSessionDto>(session);
        }

        public async Task<IEnumerable<ParkingSessionDto>> GetActiveSessionsAsync()
        {
            var activeSessions = await _unitOfWork.ParkingSessions.GetActiveSessionsAsync();
            return _mapper.Map<IEnumerable<ParkingSessionDto>>(activeSessions);
        }

        public async Task<ParkingSessionDto?> GetActiveSessionByVehicleAsync(Guid vehicleId)
        {
            var session = await _unitOfWork.ParkingSessions.GetActiveSessionByVehicleIdAsync(vehicleId);
            return session != null ? _mapper.Map<ParkingSessionDto>(session) : null;
        }

        // ✅ ESKİ HESAPLAMA KORUNDU - HİÇBİR DEĞIŞIKLIK YOK!
        private decimal CalculateParkingFee(int durationMinutes)
        {
            const decimal firstHourFee = 10.00m;
            const decimal hourlyRate = 8.00m;

            if (durationMinutes <= 60)
            {
                return firstHourFee;
            }

            var additionalHours = (int)Math.Ceiling((durationMinutes - 60) / 60.0);
            return firstHourFee + (additionalHours * hourlyRate);
        }
        /// <summary>
        /// Python'dan gelen park yerlerini sync et
        /// </summary>
        public async Task<int> SyncParkingSpacesAsync(ParkingSpaceSyncDto syncData)
        {
            int syncedCount = 0;

            foreach (var spaceDto in syncData.ParkingSpaces)
            {
                // Koordinatları JSON string olarak kaydet
                var coordinatesJson = JsonSerializer.Serialize(spaceDto.Coordinates);

                // Bu park yeri var mı kontrol et
                var existingSpace = (await _unitOfWork.ParkingSpaces.GetAllAsync())
                    .FirstOrDefault(ps => ps.SpaceNumber == spaceDto.SpaceId);

                if (existingSpace != null)
                {
                    // Güncelle
                    existingSpace.Coordinates = coordinatesJson;
                    existingSpace.Status = "available";
                    existingSpace.IsOccupied = false;

                    await _unitOfWork.ParkingSpaces.UpdateAsync(existingSpace);
                }
                else
                {
                    // Yeni ekle
                    var newSpace = new ParkingSpace
                    {
                        SpaceNumber = spaceDto.SpaceId,
                        Coordinates = coordinatesJson,
                        Status = "available",
                        IsOccupied = false,
                        FloorLevel = 1,
                        SpaceType = "standard",
                        Section = spaceDto.SpaceId.Substring(0, 1), // "A1" → "A"
                        Row = 1,
                        Column = 1,
                    };

                    await _unitOfWork.ParkingSpaces.AddAsync(newSpace);
                }

                syncedCount++;
            }

            await _unitOfWork.SaveChangesAsync();
            return syncedCount;
        }

        /// <summary>
        /// Tüm park yerlerini getir
        /// </summary>
        public async Task<List<ParkingSpaceDto>> GetAllParkingSpacesAsync()
        {
            var spaces = await _unitOfWork.ParkingSpaces.GetAllAsync();

            return spaces.Select(s => new ParkingSpaceDto
            {
                Id = s.Id,
                SpaceNumber = s.SpaceNumber,
                IsOccupied = s.IsOccupied,
                Status = s.Status,
                SpaceType = s.SpaceType,
                Section = s.Section,
                FloorLevel = s.FloorLevel,
                Coordinates = s.Coordinates,
                Row = s.Row,              // ✅ EKLENDİ
                Column = s.Column,        // ✅ EKLENDİ
                CameraId = s.CameraId     // ✅ EKLENDİ
            }).ToList();
        }
    }
}
    
