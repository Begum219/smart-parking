using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;


    namespace SmartParking.Domain.Entities
    {
        public class Vehicle : BaseEntity
        {
            public Guid UserId { get; set; }
            public string Label { get; set; } // A1, A2, A3...
            public string? Model { get; set; }
            public string? Color { get; set; }
            public string? PlateNumber { get; set; }
            public bool IsActive { get; set; }

            // Navigation Properties
            public virtual User? User { get; set; }
            public virtual ICollection<ParkingSession> ParkingSessions { get; set; }

            public Vehicle()
            {

            Label = string.Empty;
            IsActive = true;
                ParkingSessions = new HashSet<ParkingSession>();
            }
        }
    }

