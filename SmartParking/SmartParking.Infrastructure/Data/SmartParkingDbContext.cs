using Microsoft.EntityFrameworkCore;
using SmartParking.Domain.Entities;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SmartParking.Infrastructure.Data
{
    public class SmartParkingDbContext : DbContext
    {
        public SmartParkingDbContext(DbContextOptions<SmartParkingDbContext> options)
            : base(options)
        {
        }

        public DbSet<User> Users { get; set; }
        public DbSet<Vehicle> Vehicles { get; set; }
        public DbSet<Camera> Cameras { get; set; }
        public DbSet<ParkingSpace> ParkingSpaces { get; set; }
        public DbSet<ParkingSession> ParkingSessions { get; set; }
        public DbSet<Payment> Payments { get; set; }
        public DbSet<Notification> Notifications { get; set; }
        public DbSet<DetectionLog> DetectionLogs { get; set; }
        public DbSet<PricingRule> PricingRules { get; set; }
        public DbSet<Penalty> Penalties { get; set; } // ✨ YENİ EKLENDI

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);

            // User - Vehicle (Cascade OK)
            modelBuilder.Entity<Vehicle>()
                .HasOne(v => v.User)
                .WithMany(u => u.Vehicles)
                .HasForeignKey(v => v.UserId)
                .OnDelete(DeleteBehavior.Cascade);

            // User - Notification (Cascade OK)
            modelBuilder.Entity<Notification>()
                .HasOne(n => n.User)
                .WithMany(u => u.Notifications)
                .HasForeignKey(n => n.UserId)
                .OnDelete(DeleteBehavior.Cascade);

            // Vehicle - ParkingSession (Restrict to avoid cycle)
            modelBuilder.Entity<ParkingSession>()
                .HasOne(ps => ps.Vehicle)
                .WithMany(v => v.ParkingSessions)
                .HasForeignKey(ps => ps.VehicleId)
                .OnDelete(DeleteBehavior.Restrict);

            // ParkingSpace - ParkingSession (Restrict to avoid cycle)
            modelBuilder.Entity<ParkingSession>()
                .HasOne(ps => ps.ParkingSpace)
                .WithMany(p => p.ParkingSessions)
                .HasForeignKey(ps => ps.ParkingSpaceId)
                .OnDelete(DeleteBehavior.Restrict);

            // Payment - User (Restrict to avoid cycle)
            modelBuilder.Entity<Payment>()
                .HasOne(p => p.User)
                .WithMany(u => u.Payments)
                .HasForeignKey(p => p.UserId)
                .OnDelete(DeleteBehavior.Restrict);

            // Payment - Session (Restrict to avoid cycle)
            modelBuilder.Entity<Payment>()
                .HasOne(p => p.Session)
                .WithOne(s => s.Payment)
                .HasForeignKey<Payment>(p => p.SessionId)
                .OnDelete(DeleteBehavior.Restrict);

            // ✨ YENİ: Penalty - ParkingSession
            modelBuilder.Entity<Penalty>()
                .HasOne(p => p.ParkingSession)
                .WithMany(ps => ps.Penalties)
                .HasForeignKey(p => p.ParkingSessionId)
                .OnDelete(DeleteBehavior.Cascade);

            // Decimal precision (MEVCUT)
            modelBuilder.Entity<Payment>()
                .Property(p => p.Amount)
                .HasPrecision(10, 2);

            modelBuilder.Entity<ParkingSession>()
                .Property(ps => ps.TotalFee)
                .HasPrecision(10, 2);

            modelBuilder.Entity<PricingRule>()
                .Property(pr => pr.FirstHourFee)
                .HasPrecision(10, 2);

            modelBuilder.Entity<PricingRule>()
                .Property(pr => pr.HourlyRate)
                .HasPrecision(10, 2);

            modelBuilder.Entity<PricingRule>()
                .Property(pr => pr.DailyMaxFee)
                .HasPrecision(10, 2);

            // ✨ YENİ: PricingRule yeni decimal alanlar
            modelBuilder.Entity<PricingRule>()
                .Property(pr => pr.WeekendMultiplier)
                .HasPrecision(5, 2);

            modelBuilder.Entity<PricingRule>()
                .Property(pr => pr.SpecialDayMultiplier)
                .HasPrecision(5, 2);

            modelBuilder.Entity<PricingRule>()
                .Property(pr => pr.SpaceTypeMultiplier)
                .HasPrecision(5, 2);

            // ✨ YENİ: Penalty decimal precision
            modelBuilder.Entity<Penalty>()
                .Property(p => p.Amount)
                .HasPrecision(10, 2);

            modelBuilder.Entity<DetectionLog>()
                .Property(dl => dl.ConfidenceScore)
                .HasPrecision(5, 4);

            // ✨ YENİ: ParkingSpace string length ve default values
            modelBuilder.Entity<ParkingSpace>()
                .Property(ps => ps.Section)
                .HasMaxLength(10)
                .HasDefaultValue("A");

            modelBuilder.Entity<ParkingSpace>()
                .Property(ps => ps.NavigationInstructions)
                .HasMaxLength(500);

            modelBuilder.Entity<ParkingSpace>()
                .Property(ps => ps.Row)
                .HasDefaultValue(1);

            modelBuilder.Entity<ParkingSpace>()
                .Property(ps => ps.Column)
                .HasDefaultValue(1);

            // ✨ YENİ: Penalty string length
            modelBuilder.Entity<Penalty>()
                .Property(p => p.ViolationType)
                .IsRequired()
                .HasMaxLength(50);

            modelBuilder.Entity<Penalty>()
                .Property(p => p.Description)
                .HasMaxLength(500);
        }
    }
}