using HiMarket.Application.DTOs;
using HiMarket.Application.Interfaces;
using HiMarket.Domain.Entities;
using HiMarket.Domain.Enums;
using HiMarket.Infrastructure.Persistence;
using Microsoft.EntityFrameworkCore;

namespace HiMarket.Infrastructure.Services;

public class ShiftService : IShiftService
{
    private readonly HiMarketDbContext _context;

    public ShiftService(HiMarketDbContext context)
    {
        _context = context;
    }

    public async Task<ShiftDto> OpenShiftAsync(int cashierId, OpenShiftDto dto)
    {
        var existingActive = await _context.Shifts
            .FirstOrDefaultAsync(s => s.CashRegisterId == dto.CashRegisterId && !s.IsClosed && !s.IsDeleted);

        if (existingActive != null)
        {
            return await MapToDtoAsync(existingActive);
        }

        var shift = new Shift
        {
            CashRegisterId = dto.CashRegisterId,
            CashierId = cashierId,
            OpenedAt = DateTime.Now,
            OpeningFloat = dto.OpeningFloat,
            IsClosed = false
        };

        _context.Shifts.Add(shift);
        await _context.SaveChangesAsync();

        return await MapToDtoAsync(shift);
    }

    public async Task<ShiftDto?> CloseShiftAsync(CloseShiftDto dto)
    {
        var shift = await _context.Shifts
            .Include(s => s.CashRegister)
            .Include(s => s.Cashier)
            .FirstOrDefaultAsync(s => s.Id == dto.ShiftId && !s.IsDeleted);

        if (shift == null || shift.IsClosed)
            return null;

        var sales = await _context.Sales
            .Where(s => s.ShiftId == shift.Id && !s.IsCancelled && !s.IsDeleted)
            .ToListAsync();

        decimal cashSales = sales.Where(s => s.PaymentType == PaymentType.Cash).Sum(s => s.TotalAmount);
        decimal cardSales = sales.Where(s => s.PaymentType == PaymentType.CreditCard).Sum(s => s.TotalAmount);

        shift.TotalCashSales = cashSales;
        shift.TotalCardSales = cardSales;
        shift.TotalSalesCount = sales.Count;
        shift.ExpectedCash = shift.OpeningFloat + cashSales;
        shift.ActualCash = dto.ActualCash;
        shift.Difference = shift.ActualCash - shift.ExpectedCash;
        shift.ClosedAt = DateTime.Now;
        shift.IsClosed = true;
        shift.Note = dto.Note;

        await _context.SaveChangesAsync();

        return MapToDto(shift);
    }

    public async Task<ShiftDto?> GetActiveShiftByRegisterIdAsync(int registerId)
    {
        var shift = await _context.Shifts
            .Include(s => s.CashRegister)
            .Include(s => s.Cashier)
            .FirstOrDefaultAsync(s => s.CashRegisterId == registerId && !s.IsClosed && !s.IsDeleted);

        if (shift == null) return null;

        return await MapToDtoAsync(shift);
    }

    public async Task<ShiftDto?> GetShiftByIdAsync(int shiftId)
    {
        var shift = await _context.Shifts
            .Include(s => s.CashRegister)
            .Include(s => s.Cashier)
            .FirstOrDefaultAsync(s => s.Id == shiftId && !s.IsDeleted);

        if (shift == null) return null;

        return await MapToDtoAsync(shift);
    }

    private async Task<ShiftDto> MapToDtoAsync(Shift shift)
    {
        if (shift.CashRegister == null)
            await _context.Entry(shift).Reference(s => s.CashRegister).LoadAsync();
        if (shift.Cashier == null)
            await _context.Entry(shift).Reference(s => s.Cashier).LoadAsync();

        var sales = await _context.Sales
            .Where(s => s.ShiftId == shift.Id && !s.IsCancelled && !s.IsDeleted)
            .ToListAsync();

        decimal cashSales = sales.Where(s => s.PaymentType == PaymentType.Cash).Sum(s => s.TotalAmount);
        decimal cardSales = sales.Where(s => s.PaymentType == PaymentType.CreditCard).Sum(s => s.TotalAmount);
        decimal expectedCash = shift.OpeningFloat + cashSales;

        return new ShiftDto
        {
            Id = shift.Id,
            CashRegisterId = shift.CashRegisterId,
            CashRegisterName = shift.CashRegister?.Name ?? string.Empty,
            CashierId = shift.CashierId,
            CashierName = shift.Cashier?.FullName ?? string.Empty,
            OpenedAt = shift.OpenedAt,
            ClosedAt = shift.ClosedAt,
            OpeningFloat = shift.OpeningFloat,
            TotalCashSales = cashSales,
            TotalCardSales = cardSales,
            TotalSalesCount = sales.Count,
            ExpectedCash = expectedCash,
            ActualCash = shift.ActualCash,
            Difference = shift.IsClosed ? shift.Difference : (shift.ActualCash - expectedCash),
            IsClosed = shift.IsClosed,
            Note = shift.Note
        };
    }

    private ShiftDto MapToDto(Shift shift)
    {
        return new ShiftDto
        {
            Id = shift.Id,
            CashRegisterId = shift.CashRegisterId,
            CashRegisterName = shift.CashRegister?.Name ?? string.Empty,
            CashierId = shift.CashierId,
            CashierName = shift.Cashier?.FullName ?? string.Empty,
            OpenedAt = shift.OpenedAt,
            ClosedAt = shift.ClosedAt,
            OpeningFloat = shift.OpeningFloat,
            TotalCashSales = shift.TotalCashSales,
            TotalCardSales = shift.TotalCardSales,
            TotalSalesCount = shift.TotalSalesCount,
            ExpectedCash = shift.ExpectedCash,
            ActualCash = shift.ActualCash,
            Difference = shift.Difference,
            IsClosed = shift.IsClosed,
            Note = shift.Note
        };
    }
}
