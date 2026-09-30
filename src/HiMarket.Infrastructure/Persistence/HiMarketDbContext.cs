using HiMarket.Domain.Entities;
using Microsoft.EntityFrameworkCore;

namespace HiMarket.Infrastructure.Persistence;

public class HiMarketDbContext : DbContext
{
    public HiMarketDbContext(DbContextOptions<HiMarketDbContext> options) : base(options)
    {
    }

    public DbSet<User> Users => Set<User>();
    public DbSet<Category> Categories => Set<Category>();
    public DbSet<Product> Products => Set<Product>();
    public DbSet<CashRegister> CashRegisters => Set<CashRegister>();
    public DbSet<Shift> Shifts => Set<Shift>();
    public DbSet<Sale> Sales => Set<Sale>();
    public DbSet<SaleItem> SaleItems => Set<SaleItem>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Product Configurations
        modelBuilder.Entity<Product>(entity =>
        {
            entity.HasIndex(p => p.Barcode).IsUnique();
            entity.Property(p => p.BuyPrice).HasPrecision(18, 2);
            entity.Property(p => p.SellPrice).HasPrecision(18, 2);
            entity.Property(p => p.VatRate).HasPrecision(5, 2);
            entity.Property(p => p.StockQuantity).HasPrecision(18, 3);
            entity.Property(p => p.MinStockLevel).HasPrecision(18, 3);
        });

        // Shift Configurations
        modelBuilder.Entity<Shift>(entity =>
        {
            entity.Property(s => s.OpeningFloat).HasPrecision(18, 2);
            entity.Property(s => s.TotalCashSales).HasPrecision(18, 2);
            entity.Property(s => s.TotalCardSales).HasPrecision(18, 2);
            entity.Property(s => s.ExpectedCash).HasPrecision(18, 2);
            entity.Property(s => s.ActualCash).HasPrecision(18, 2);
            entity.Property(s => s.Difference).HasPrecision(18, 2);

            entity.HasOne(s => s.Cashier)
                  .WithMany()
                  .HasForeignKey(s => s.CashierId)
                  .OnDelete(DeleteBehavior.Restrict);

            entity.HasOne(s => s.CashRegister)
                  .WithMany()
                  .HasForeignKey(s => s.CashRegisterId)
                  .OnDelete(DeleteBehavior.Restrict);
        });

        // CashRegister Configurations
        modelBuilder.Entity<CashRegister>(entity =>
        {
            entity.HasOne(c => c.CurrentShift)
                  .WithMany()
                  .HasForeignKey(c => c.CurrentShiftId)
                  .OnDelete(DeleteBehavior.Restrict);
        });

        // Sale Configurations
        modelBuilder.Entity<Sale>(entity =>
        {
            entity.HasIndex(s => s.ReceiptNumber).IsUnique();
            entity.Property(s => s.SubTotal).HasPrecision(18, 2);
            entity.Property(s => s.TotalVatAmount).HasPrecision(18, 2);
            entity.Property(s => s.DiscountAmount).HasPrecision(18, 2);
            entity.Property(s => s.TotalAmount).HasPrecision(18, 2);
            entity.Property(s => s.CashPaid).HasPrecision(18, 2);
            entity.Property(s => s.ChangeGiven).HasPrecision(18, 2);

            entity.HasOne(s => s.Cashier)
                  .WithMany()
                  .HasForeignKey(s => s.CashierId)
                  .OnDelete(DeleteBehavior.Restrict);

            entity.HasOne(s => s.Shift)
                  .WithMany(sh => sh.Sales)
                  .HasForeignKey(s => s.ShiftId)
                  .OnDelete(DeleteBehavior.Restrict);
        });

        // SaleItem Configurations
        modelBuilder.Entity<SaleItem>(entity =>
        {
            entity.Property(si => si.Quantity).HasPrecision(18, 3);
            entity.Property(si => si.UnitPrice).HasPrecision(18, 2);
            entity.Property(si => si.VatRate).HasPrecision(5, 2);
            entity.Property(si => si.VatAmount).HasPrecision(18, 2);
            entity.Property(si => si.TotalPrice).HasPrecision(18, 2);

            entity.HasOne(si => si.Sale)
                  .WithMany(s => s.SaleItems)
                  .HasForeignKey(si => si.SaleId)
                  .OnDelete(DeleteBehavior.Cascade);
        });
    }
}
