namespace HiMarket.Application.DTOs;

public record OpenShiftDto(
    int CashRegisterId,
    decimal OpeningFloat
);

public record CloseShiftDto(
    int ShiftId,
    decimal ActualCash,
    string? Note
);

public class ShiftDto
{
    public int Id { get; set; }
    public int CashRegisterId { get; set; }
    public string CashRegisterName { get; set; } = string.Empty;

    public int CashierId { get; set; }
    public string CashierName { get; set; } = string.Empty;

    public DateTime OpenedAt { get; set; }
    public DateTime? ClosedAt { get; set; }

    public decimal OpeningFloat { get; set; }
    public decimal TotalCashSales { get; set; }
    public decimal TotalCardSales { get; set; }
    public int TotalSalesCount { get; set; }

    public decimal ExpectedCash { get; set; }
    public decimal ActualCash { get; set; }
    public decimal Difference { get; set; }

    public bool IsClosed { get; set; }
    public string? Note { get; set; }
}
