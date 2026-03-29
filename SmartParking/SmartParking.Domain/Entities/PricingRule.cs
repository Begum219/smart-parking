using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SmartParking.Domain.Entities
{
    public class PricingRule : BaseEntity
    {
        // ✅ MEVCUT ALANLAR (Korundu)
        public string RuleName { get; set; } = string.Empty;
        public string SpaceType { get; set; } = "standard";
        public decimal FirstHourFee { get; set; }
        public decimal HourlyRate { get; set; }
        public decimal? DailyMaxFee { get; set; }
        public bool IsActive { get; set; }
        public DateTime ValidFrom { get; set; }
        public DateTime? ValidUntil { get; set; }

        // ✨ YENİ EKLEMELER - Zaman Dilimli Ücretlendirme
        public TimeSpan? StartTime { get; set; } // Örn: 08:00
        public TimeSpan? EndTime { get; set; }   // Örn: 18:00

        // ✨ Hafta sonu fiyatlandırması
        public bool IsWeekendRate { get; set; }
        public decimal WeekendMultiplier { get; set; } // Hafta sonu x1.5

        // ✨ Özel günler (bayram, yılbaşı)
        public bool IsSpecialDay { get; set; }
        public decimal SpecialDayMultiplier { get; set; }

        // ✨ Park yeri tipine göre çarpan (VIP x2.0 gibi)
        public decimal SpaceTypeMultiplier { get; set; }

        public PricingRule()
        {
            // ✅ MEVCUT (Korundu)
            SpaceType = "standard";
            IsActive = true;
            ValidFrom = DateTime.UtcNow;

            // ✨ YENİ - Varsayılan değerler
            WeekendMultiplier = 1.0m;
            SpecialDayMultiplier = 1.0m;
            SpaceTypeMultiplier = 1.0m;
            IsWeekendRate = false;
            IsSpecialDay = false;
        }
    }
}