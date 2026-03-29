using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SmartParking.Application.DTOs
{
    public class CreateVehicleDto
    {
        public string Label { get; set; } = string.Empty;
        public string? Model { get; set; }
        public string? Color { get; set; }
        public string? PlateNumber { get; set; }
    }
}
