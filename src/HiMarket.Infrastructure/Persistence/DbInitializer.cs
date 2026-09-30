using HiMarket.Domain.Entities;
using HiMarket.Domain.Enums;
using Microsoft.EntityFrameworkCore;

namespace HiMarket.Infrastructure.Persistence;

public static class DbInitializer
{
    public static async Task SeedAsync(HiMarketDbContext context)
    {
        await context.Database.MigrateAsync();

        // 1. Seed Users
        if (!await context.Users.AnyAsync())
        {
            var adminUser = new User
            {
                FullName = "Mağaza Yöneticisi",
                Email = "admin@himarket.com",
                PasswordHash = BCrypt.Net.BCrypt.HashPassword("Admin123!"),
                PinCode = "9999",
                Role = UserRole.Admin
            };

            var cashierUser = new User
            {
                FullName = "Ahmet Yılmaz (Kasiyer)",
                Email = "kasiyer1@himarket.com",
                PasswordHash = BCrypt.Net.BCrypt.HashPassword("Kasiyer123!"),
                PinCode = "1234",
                Role = UserRole.Cashier
            };

            await context.Users.AddRangeAsync(adminUser, cashierUser);
            await context.SaveChangesAsync();
        }

        // 2. Seed Cash Registers
        if (!await context.CashRegisters.AnyAsync())
        {
            var register1 = new CashRegister
            {
                Name = "Kasa 1 (Ana Kasa)",
                RegisterCode = "KASA-01",
                IsActive = true
            };

            await context.CashRegisters.AddAsync(register1);
            await context.SaveChangesAsync();
        }

        // 3. Seed Categories
        if (!await context.Categories.AnyAsync())
        {
            var categories = new List<Category>
            {
                new Category { Name = "Fırın & Unlu Mamüller", DisplayOrder = 1 },
                new Category { Name = "Temel Gıda", DisplayOrder = 2 },
                new Category { Name = "İçecekler", DisplayOrder = 3 },
                new Category { Name = "Şarküteri & Süt Ürünleri", DisplayOrder = 4 },
                new Category { Name = "Manav & Sebze/Meyve", DisplayOrder = 5 }
            };

            await context.Categories.AddRangeAsync(categories);
            await context.SaveChangesAsync();
        }

        // 4. Seed Products
        if (!await context.Products.AnyAsync())
        {
            var bakeryCat = await context.Categories.FirstAsync(c => c.Name.Contains("Fırın"));
            var gidaCat = await context.Categories.FirstAsync(c => c.Name.Contains("Temel Gıda"));
            var drinkCat = await context.Categories.FirstAsync(c => c.Name.Contains("İçecekler"));
            var dairyCat = await context.Categories.FirstAsync(c => c.Name.Contains("Şarküteri"));
            var manavCat = await context.Categories.FirstAsync(c => c.Name.Contains("Manav"));

            var products = new List<Product>
            {
                new Product
                {
                    Barcode = "8690000000010",
                    Name = "Ekmek 200g",
                    CategoryId = bakeryCat.Id,
                    BuyPrice = 8.00m,
                    SellPrice = 10.00m,
                    VatRate = 1.00m,
                    IsWeighted = false,
                    Unit = "Adet",
                    StockQuantity = 500,
                    IsQuickButton = true,
                    QuickButtonOrder = 1
                },
                new Product
                {
                    Barcode = "8690000000027",
                    Name = "Büyük Boy Poşet",
                    CategoryId = gidaCat.Id,
                    BuyPrice = 0.10m,
                    SellPrice = 0.50m,
                    VatRate = 20.00m,
                    IsWeighted = false,
                    Unit = "Adet",
                    StockQuantity = 10000,
                    IsQuickButton = true,
                    QuickButtonOrder = 2
                },
                new Product
                {
                    Barcode = "8690504018003",
                    Name = "Su 0.5L Pet",
                    CategoryId = drinkCat.Id,
                    BuyPrice = 3.50m,
                    SellPrice = 6.00m,
                    VatRate = 10.00m,
                    IsWeighted = false,
                    Unit = "Adet",
                    StockQuantity = 200,
                    IsQuickButton = true,
                    QuickButtonOrder = 3
                },
                new Product
                {
                    Barcode = "8690504000123",
                    Name = "Tam Yağlı Süt 1L",
                    CategoryId = dairyCat.Id,
                    BuyPrice = 26.00m,
                    SellPrice = 34.50m,
                    VatRate = 1.00m,
                    IsWeighted = false,
                    Unit = "Adet",
                    StockQuantity = 80,
                    IsQuickButton = false
                },
                new Product
                {
                    Barcode = "2700001014502",
                    Name = "Amasya Elması",
                    CategoryId = manavCat.Id,
                    BuyPrice = 20.00m,
                    SellPrice = 35.00m,
                    VatRate = 1.00m,
                    IsWeighted = true,
                    Unit = "KG",
                    StockQuantity = 150.000m,
                    IsQuickButton = true,
                    QuickButtonOrder = 4
                }
            };

            await context.Products.AddRangeAsync(products);
            await context.SaveChangesAsync();
        }
    }
}
