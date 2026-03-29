using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SmartParking.Domain.Entities
{
    public class Camera : BaseEntity
    {
        public string Name { get; set; }
        public string? Location { get; set; }
        public string? IpAddress { get; set; }
        public string Status { get; set; } // "active", "inactive", "maintenance"
        public string? CoverageArea { get; set; } // JSON string

        // Navigation Properties
        public virtual ICollection<ParkingSpace> ParkingSpaces { get; set; }
        public virtual ICollection<DetectionLog> DetectionLogs { get; set; }

        public Camera()
        {
            Status = "active";
            ParkingSpaces = new HashSet<ParkingSpace>();
            DetectionLogs = new HashSet<DetectionLog>();
        }
    }
}
