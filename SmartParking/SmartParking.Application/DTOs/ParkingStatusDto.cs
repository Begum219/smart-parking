using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SmartParking.Application.DTOs
{
    public class ParkingStatusDto
    {
        public int TotalSpaces { get; set; }
        public int OccupiedSpaces { get; set; }
        public int AvailableSpaces { get; set; }
        public double OccupancyRate { get; set; }
        public List<ParkingSpaceDto> Spaces { get; set; } = new();
    }
}
