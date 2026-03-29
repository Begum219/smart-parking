using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SmartParking.Application.DTOs
{
    public class VehicleDto
    {
        public Guid Id { get; set; }
        public Guid UserId { get; set; }
        public string Label { get; set; } = string.Empty;
        public string? Model { get; set; }
        public string? Color { get; set; }
        public string? PlateNumber { get; set; }
        public bool IsActive { get; set; }
    }
}