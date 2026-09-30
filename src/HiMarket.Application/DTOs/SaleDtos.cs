using HiMarket.Domain.Enums;

namespace HiMarket.Application.DTOs;

public class CreateSaleItemDto
{
    public int ProductId { get; set; }
    public decimal Quantity { get; set; }
    public decimal UnitPrice { get; set; }
}

public class CreateSaleDto
{
    public int ShiftId { get; set; }
    public PaymentType PaymentType { get; set; }
    public decimal CashPaid { get; set; }
    public decimal DiscountAmount { get; set; } = 0;
    public List<CreateSaleItemDto> Items { get; set; } = new();
}

public class SaleDto
{
    public int Id { get; set; }
    public string ReceiptNumber { get; set; } = string.Empty;
    public DateTime CreatedAt { get; set; }

    public int ShiftId { get; set; }
    public string CashierName { get; set; } = string.Empty;

    public decimal SubTotal { get; set; }
    public decimal TotalVatAmount { get; set; }
    public decimal DiscountAmount { get; set; }
    public decimal TotalAmount { get; set; }

    public PaymentType PaymentType { get; set; }
    public decimal CashPaid { get; set; }
    public decimal ChangeGiven { get; set; }

    public bool IsCancelled { get; set; }
    public List<SaleItemDto> Items { get; set; } = new();
}

public class SaleItemDto
{
    public int ProductId { get; set; }
    public string ProductName { get; set; } = string.Empty;
    public string Barcode { get; set; } = string.Empty;

    public decimal Quantity { get; set; }
    public decimal UnitPrice { get; set; }
    public decimal VatRate { get; set; }
    public decimal VatAmount { get; set; }
    public decimal TotalPrice { get; set; }
}
