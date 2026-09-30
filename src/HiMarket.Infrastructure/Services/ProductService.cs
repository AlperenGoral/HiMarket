using HiMarket.Application.DTOs;
using HiMarket.Application.Interfaces;
using HiMarket.Domain.Entities;
using HiMarket.Infrastructure.Persistence;
using Mapster;
using Microsoft.EntityFrameworkCore;

namespace HiMarket.Infrastructure.Services;

public class ProductService : IProductService
{
    private readonly HiMarketDbContext _context;

    public ProductService(HiMarketDbContext context)
    {
        _context = context;
    }

    public async Task<List<ProductDto>> GetAllProductsAsync()
    {
        var products = await _context.Products
            .Include(p => p.Category)
            .Where(p => p.IsActive && !p.IsDeleted)
            .OrderBy(p => p.Name)
            .ToListAsync();

        return products.Adapt<List<ProductDto>>();
    }

    public async Task<ProductDto?> GetProductByIdAsync(int id)
    {
        var product = await _context.Products
            .Include(p => p.Category)
            .FirstOrDefaultAsync(p => p.Id == id && p.IsActive && !p.IsDeleted);

        return product?.Adapt<ProductDto>();
    }

    public async Task<BarcodeSearchResultDto?> SearchByBarcodeAsync(string barcode)
    {
        if (string.IsNullOrWhiteSpace(barcode))
            return null;

        barcode = barcode.Trim();

        // 1. Standart Barkod Sorgulama (EAN-13, EAN-8 vb.)
        var product = await _context.Products
            .Include(p => p.Category)
            .FirstOrDefaultAsync(p => (p.Barcode == barcode || p.SecondaryBarcode == barcode) && p.IsActive && !p.IsDeleted);

        if (product != null)
        {
            return new BarcodeSearchResultDto
            {
                Product = product.Adapt<ProductDto>(),
                Quantity = 1.0m,
                IsWeightedBarcode = false
            };
        }

        // 2. Terazi / Tartılı Ürün Barkodu Çözümleme (27 veya 28 ile başlayan 13 haneli barkodlar)
        // Format: [27 veya 28] [5 Hane Ürün Kodu] [5 Hane Gramaj/Fiyat] [1 Hane Kontrol]
        // Örn: 27 00001 01450 2 -> Ürün Kodu: 00001, Gramaj: 1450 Gram (1.450 KG)
        if (barcode.Length == 13 && (barcode.StartsWith("27") || barcode.StartsWith("28")))
        {
            string productCode = barcode.Substring(2, 5);
            string rawValue = barcode.Substring(7, 5);

            var weightedProduct = await _context.Products
                .Include(p => p.Category)
                .FirstOrDefaultAsync(p => p.IsWeighted && p.Barcode.Contains(productCode) && p.IsActive && !p.IsDeleted);

            if (weightedProduct != null && decimal.TryParse(rawValue, out decimal parsedValue))
            {
                decimal calculatedQuantity = parsedValue / 1000.0m;

                return new BarcodeSearchResultDto
                {
                    Product = weightedProduct.Adapt<ProductDto>(),
                    Quantity = Math.Round(calculatedQuantity, 3),
                    IsWeightedBarcode = true
                };
            }
        }

        return null;
    }

    public async Task<List<ProductDto>> GetQuickButtonsAsync()
    {
        var quickProducts = await _context.Products
            .Include(p => p.Category)
            .Where(p => p.IsQuickButton && p.IsActive && !p.IsDeleted)
            .OrderBy(p => p.QuickButtonOrder)
            .ToListAsync();

        return quickProducts.Adapt<List<ProductDto>>();
    }

    public async Task<List<ProductDto>> GetByCategoryAsync(int categoryId)
    {
        var products = await _context.Products
            .Include(p => p.Category)
            .Where(p => p.CategoryId == categoryId && p.IsActive && !p.IsDeleted)
            .OrderBy(p => p.Name)
            .ToListAsync();

        return products.Adapt<List<ProductDto>>();
    }

    public async Task<ProductDto> CreateProductAsync(CreateProductDto dto)
    {
        var product = dto.Adapt<Product>();
        product.CreatedAt = DateTime.Now;

        await _context.Products.AddAsync(product);
        await _context.SaveChangesAsync();

        return (await GetProductByIdAsync(product.Id))!;
    }

    public async Task<ProductDto?> UpdateProductAsync(int id, CreateProductDto dto)
    {
        var product = await _context.Products.FirstOrDefaultAsync(p => p.Id == id && !p.IsDeleted);
        if (product == null) return null;

        dto.Adapt(product);
        product.UpdatedAt = DateTime.Now;

        await _context.SaveChangesAsync();
        return await GetProductByIdAsync(id);
    }

    public async Task<bool> DeleteProductAsync(int id)
    {
        var product = await _context.Products.FirstOrDefaultAsync(p => p.Id == id && !p.IsDeleted);
        if (product == null) return false;

        product.IsDeleted = true;
        product.UpdatedAt = DateTime.Now;

        await _context.SaveChangesAsync();
        return true;
    }
}
