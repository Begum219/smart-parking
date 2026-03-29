using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SmartParking.Domain.Entities
{
    public class DetectionLog : BaseEntity
    {
        public Guid CameraId { get; set; }
        public string DetectionType { get; set; } = string.Empty; // "vehicle", "label"
        public string? DetectedValue { get; set; }
        public decimal? ConfidenceScore { get; set; }
        public string? ImageUrl { get; set; }
        public string? BoundingBox { get; set; } // JSON string
        public DateTime DetectionTime { get; set; }

        // Navigation Property
        public virtual Camera ?Camera { get; set; }

        public DetectionLog()
        {
            DetectionTime = DateTime.UtcNow;
        }
    }
}