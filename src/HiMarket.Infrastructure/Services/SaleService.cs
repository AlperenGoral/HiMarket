using HiMarket.Application.DTOs;
using HiMarket.Application.Interfaces;
using HiMarket.Domain.Entities;
using HiMarket.Domain.Enums;
using HiMarket.Infrastructure.Persistence;
using Microsoft.EntityFrameworkCore;

namespace HiMarket.Infrastructure.Services;

public class SaleService : ISaleService
{
    private readonly HiMarketDbContext _context;

    public SaleService(HiMarketDbContext context)
    {
        _context = context;
    }

    public async Task<SaleDto> ProcessSaleAsync(int cashierId, CreateSaleDto dto)
    {
        var shift = await _context.Shifts
            .Include(s => s.Cashier)
            .FirstOrDefaultAsync(s => s.Id == dto.ShiftId && !s.IsClosed && !s.IsDeleted);

        if (shift == null)
            throw new InvalidOperationException("Aktif vardiya bulunamadı veya vardiya kapalı!");

        string receiptNumber = $"REC-{DateTime.Now:yyyyMMddHHmmss}-{Random.Shared.Next(1000, 9999)}";

        var sale = new Sale
        {
            ReceiptNumber = receiptNumber,
            ShiftId = dto.ShiftId,
            CashierId = cashierId,
            PaymentType = dto.PaymentType,
            CashPaid = dto.CashPaid,
            DiscountAmount = dto.DiscountAmount,
            CreatedAt = DateTime.Now,
            IsCancelled = false
        };

        decimal subTotal = 0;
        decimal totalVat = 0;

        foreach (var itemDto in dto.Items)
        {
            var product = await _context.Products.FindAsync(itemDto.ProductId);
            if (product == null) continue;

            decimal lineTotal = itemDto.Quantity * itemDto.UnitPrice;
            decimal vatRate = product.VatRate;
            // Vat included calculation: lineTotal * (vatRate / (100 + vatRate))
            decimal vatAmount = Math.Round(lineTotal * (vatRate / (100m + vatRate)), 2);

            subTotal += lineTotal;
            totalVat += vatAmount;

            // Stock deduction
            product.StockQuantity -= itemDto.Quantity;
            product.UpdatedAt = DateTime.Now;

            var saleItem = new SaleItem
            {
                ProductId = product.Id,
                Quantity = itemDto.Quantity,
                UnitPrice = itemDto.UnitPrice,
                VatRate = vatRate,
                VatAmount = vatAmount,
                TotalPrice = lineTotal
            };

            sale.SaleItems.Add(saleItem);
        }

        sale.SubTotal = subTotal;
        sale.TotalVatAmount = totalVat;
        sale.TotalAmount = Math.Max(0, subTotal - dto.DiscountAmount);

        if (dto.PaymentType == PaymentType.Cash)
        {
            sale.ChangeGiven = Math.Max(0, dto.CashPaid - sale.TotalAmount);
        }
        else
        {
            sale.CashPaid = sale.TotalAmount;
            sale.ChangeGiven = 0;
        }

        _context.Sales.Add(sale);
        await _context.SaveChangesAsync();

        return MapToDto(sale, shift.Cashier?.FullName ?? "Kasiyer");
    }

    public async Task<SaleDto?> GetSaleByReceiptNumberAsync(string receiptNumber)
    {
        var sale = await _context.Sales
            .Include(s => s.Cashier)
            .Include(s => s.SaleItems)
                .ThenInclude(i => i.Product)
            .FirstOrDefaultAsync(s => s.ReceiptNumber == receiptNumber && !s.IsDeleted);

        if (sale == null) return null;

        return MapToDto(sale, sale.Cashier?.FullName ?? "Kasiyer");
    }

    public async Task<bool> CancelSaleAsync(int saleId, int supervisorId, string reason)
    {
        var sale = await _context.Sales
            .Include(s => s.SaleItems)
            .FirstOrDefaultAsync(s => s.Id == saleId && !s.IsDeleted);

        if (sale == null || sale.IsCancelled)
            return false;

        sale.IsCancelled = true;
        sale.CancelledAt = DateTime.Now;
        sale.CancelledBySupervisorId = supervisorId;
        sale.CancellationReason = reason;

        // Restore stock
        foreach (var item in sale.SaleItems)
        {
            var product = await _context.Products.FindAsync(item.ProductId);
            if (product != null)
            {
                product.StockQuantity += item.Quantity;
                product.UpdatedAt = DateTime.Now;
            }
        }

        await _context.SaveChangesAsync();
        return true;
    }

    private SaleDto MapToDto(Sale sale, string cashierName)
    {
        return new SaleDto
        {
            Id = sale.Id,
            ReceiptNumber = sale.ReceiptNumber,
            CreatedAt = sale.CreatedAt,
            ShiftId = sale.ShiftId,
            CashierName = cashierName,
            SubTotal = sale.SubTotal,
            TotalVatAmount = sale.TotalVatAmount,
            DiscountAmount = sale.DiscountAmount,
            TotalAmount = sale.TotalAmount,
            PaymentType = sale.PaymentType,
            CashPaid = sale.CashPaid,
            ChangeGiven = sale.ChangeGiven,
            IsCancelled = sale.IsCancelled,
            Items = sale.SaleItems.Select(i => new SaleItemDto
            {
                ProductId = i.ProductId,
                ProductName = i.Product?.Name ?? "Ürün",
                Barcode = i.Product?.Barcode ?? "",
                Quantity = i.Quantity,
                UnitPrice = i.UnitPrice,
                VatRate = i.VatRate,
                VatAmount = i.VatAmount,
                TotalPrice = i.TotalPrice
            }).ToList()
        };
    }
}
