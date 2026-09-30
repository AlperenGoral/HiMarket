namespace HiMarket.Domain.Entities;

public class Shift : BaseEntity
{
    public int CashRegisterId { get; set; }
    public CashRegister CashRegister { get; set; } = null!;

    public int CashierId { get; set; }
    public User Cashier { get; set; } = null!;

    public DateTime OpenedAt { get; set; } = DateTime.Now;
    public DateTime? ClosedAt { get; set; }

    public decimal OpeningFloat { get; set; } = 0;

    public decimal TotalCashSales { get; set; } = 0;
    public decimal TotalCardSales { get; set; } = 0;
    public int TotalSalesCount { get; set; } = 0;

    public decimal ExpectedCash { get; set; } = 0;
    public decimal ActualCash { get; set; } = 0;
    public decimal Difference { get; set; } = 0;

    public bool IsClosed { get; set; } = false;
    public string? Note { get; set; }

    public ICollection<Sale> Sales { get; set; } = new List<Sale>();
}
