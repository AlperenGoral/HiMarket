using HiMarket.Domain.Enums;

namespace HiMarket.Domain.Entities;

public class Sale : BaseEntity
{
    public string ReceiptNumber { get; set; } = string.Empty;

    public int ShiftId { get; set; }
    public Shift Shift { get; set; } = null!;

    public int CashierId { get; set; }
    public User Cashier { get; set; } = null!;

    public decimal SubTotal { get; set; }
    public decimal TotalVatAmount { get; set; }
    public decimal DiscountAmount { get; set; } = 0;
    public decimal TotalAmount { get; set; }

    public PaymentType PaymentType { get; set; } = PaymentType.Cash;
    public decimal CashPaid { get; set; } = 0;
    public decimal ChangeGiven { get; set; } = 0;

    public bool IsCancelled { get; set; } = false;
    public DateTime? CancelledAt { get; set; }
    public int? CancelledBySupervisorId { get; set; }
    public string? CancellationReason { get; set; }

    public ICollection<SaleItem> SaleItems { get; set; } = new List<SaleItem>();
}
