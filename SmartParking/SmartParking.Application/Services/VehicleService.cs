using AutoMapper;
using SmartParking.Application.DTOs;
using SmartParking.Application.Interfaces;
using SmartParking.Domain.Entities;
using SmartParking.Domain.Interfaces;

namespace SmartParking.Application.Services
{
    public class VehicleService : IVehicleService
    {
        private readonly IUnitOfWork _unitOfWork;
        private readonly IMapper _mapper;

        public VehicleService(IUnitOfWork unitOfWork, IMapper mapper)
        {
            _unitOfWork = unitOfWork;
            _mapper = mapper;
        }

        public async Task<IEnumerable<VehicleDto>> GetUserVehiclesAsync(Guid userId)
        {
            var vehicles = await _unitOfWork.Vehicles.GetByUserIdAsync(userId);
            return _mapper.Map<IEnumerable<VehicleDto>>(vehicles);
        }

        public async Task<VehicleDto> GetVehicleByIdAsync(Guid vehicleId)
        {
            var vehicle = await _unitOfWork.Vehicles.GetByIdAsync(vehicleId);
            if (vehicle == null)
            {
                throw new Exception("Vehicle not found");
            }
            return _mapper.Map<VehicleDto>(vehicle);
        }

        public async Task<VehicleDto> CreateVehicleAsync(Guid userId, CreateVehicleDto createVehicleDto)
        {
            // Label kontrolü
            var existingVehicle = await _unitOfWork.Vehicles.GetByLabelAsync(createVehicleDto.Label);
            if (existingVehicle != null)
            {
                throw new Exception("Vehicle label already exists");
            }

            var vehicle = _mapper.Map<Vehicle>(createVehicleDto);
            vehicle.UserId = userId;

            await _unitOfWork.Vehicles.AddAsync(vehicle);
            await _unitOfWork.SaveChangesAsync();

            return _mapper.Map<VehicleDto>(vehicle);
        }

        public async Task<VehicleDto> UpdateVehicleAsync(Guid vehicleId, CreateVehicleDto updateVehicleDto)
        {
            var vehicle = await _unitOfWork.Vehicles.GetByIdAsync(vehicleId);
            if (vehicle == null)
            {
                throw new Exception("Vehicle not found");
            }

            // ✅ Label (Marka) eklendi
            vehicle.Label = updateVehicleDto.Label;
            vehicle.Model = updateVehicleDto.Model;
            vehicle.Color = updateVehicleDto.Color;
            vehicle.PlateNumber = updateVehicleDto.PlateNumber;
            vehicle.UpdatedAt = DateTime.UtcNow; // ✅ UpdatedAt eklendi

            await _unitOfWork.Vehicles.UpdateAsync(vehicle);
            await _unitOfWork.SaveChangesAsync();

            return _mapper.Map<VehicleDto>(vehicle);
        }

        public async Task DeleteVehicleAsync(Guid vehicleId)
        {
            await _unitOfWork.Vehicles.DeleteAsync(vehicleId);
            await _unitOfWork.SaveChangesAsync();
        }
    }
}