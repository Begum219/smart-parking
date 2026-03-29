using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Design;

namespace SmartParking.Infrastructure.Data
{
    public class SmartParkingDbContextFactory : IDesignTimeDbContextFactory<SmartParkingDbContext>
    {
        public SmartParkingDbContext CreateDbContext(string[] args)
        {
            var optionsBuilder = new DbContextOptionsBuilder<SmartParkingDbContext>();
            optionsBuilder.UseSqlServer("Server=localhost;Database=SmartParkingDB;Trusted_Connection=True;TrustServerCertificate=True;");

            return new SmartParkingDbContext(optionsBuilder.Options);
        }
    }
}