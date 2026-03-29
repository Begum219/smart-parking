using AutoMapper;
using SmartParking.Application.DTOs;
using SmartParking.Application.DTOs.Auth;
using SmartParking.Domain.Entities;

namespace SmartParking.Application.Mappings
{
    public class MappingProfile : Profile
    {
        public MappingProfile()
        {
            // User Mappings
            CreateMap<User, UserDto>()
                .ForMember(dest => dest.Role, opt => opt.MapFrom(src => src.Role.ToString())); // ✅ EKLENDİ

            CreateMap<RegisterDto, User>()
                .ForMember(dest => dest.PasswordHash, opt => opt.Ignore());

            // Vehicle Mappings
            CreateMap<Vehicle, VehicleDto>();
            CreateMap<CreateVehicleDto, Vehicle>();

            // ParkingSpace Mappings
            CreateMap<ParkingSpace, ParkingSpaceDto>();

            // ParkingSession Mappings
            CreateMap<ParkingSession, ParkingSessionDto>()
                .ForMember(dest => dest.VehicleLabel, opt => opt.MapFrom(src => src.Vehicle.Label))
                .ForMember(dest => dest.SpaceNumber, opt => opt.MapFrom(src => src.ParkingSpace.SpaceNumber));

            // Payment Mappings
            CreateMap<Payment, PaymentDto>();
        }
    }
}