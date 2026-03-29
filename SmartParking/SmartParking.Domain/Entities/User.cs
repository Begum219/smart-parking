using SmartParking.Domain.Enums;
namespace SmartParking.Domain.Entities
{
    public class User : BaseEntity
    {
        public string Name { get; set; }
        public string Email { get; set; }
        public string PasswordHash { get; set; }
        public string? Phone { get; set; }
        public UserRole Role { get; set; } // "user", "admin", "manager"
        public bool IsActive { get; set; }

        // Navigation Properties
        public virtual ICollection<Vehicle> Vehicles { get; set; }
        public virtual ICollection<Payment> Payments { get; set; }
        public virtual ICollection<Notification> Notifications { get; set; }

        public User()
        {
            Role = UserRole.User; 
            IsActive = true;
            Vehicles = new HashSet<Vehicle>();
            Payments = new HashSet<Payment>();
            Notifications = new HashSet<Notification>();
        }
    }
}