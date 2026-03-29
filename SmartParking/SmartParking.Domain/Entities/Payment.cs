using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SmartParking.Domain.Entities
{
    public class Payment : BaseEntity
    {
        public Guid SessionId { get; set; }
        public Guid UserId { get; set; }
        public decimal Amount { get; set; }
        public string? PaymentMethod { get; set; } // "cash", "credit_card", "debit_card"
        public string PaymentStatus { get; set; } // "pending", "completed", "failed"
        public string? TransactionId { get; set; }
        public DateTime PaymentTime { get; set; }

        // Navigation Properties
        public virtual ParkingSession ?Session { get; set; }
        public virtual User ?User { get; set; }

        public Payment()
        {
            PaymentStatus = "completed";
            PaymentTime = DateTime.UtcNow;
        }
    }
}