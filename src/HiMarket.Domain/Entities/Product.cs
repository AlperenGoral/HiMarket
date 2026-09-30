namespace HiMarket.Domain.Entities;

public class Product : BaseEntity
{
    public string Barcode { get; set; } = string.Empty;
    public string? SecondaryBarcode { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? ImageUrl { get; set; }

    public int CategoryId { get; set; }
    public Category Category { get; set; } = null!;

    public decimal BuyPrice { get; set; }
    public decimal SellPrice { get; set; }
    public decimal VatRate { get; set; } = 10;

    public bool IsWeighted { get; set; } = false;
    public string Unit { get; set; } = "Adet";

    public decimal StockQuantity { get; set; } = 0;
    public decimal MinStockLevel { get; set; } = 5;

    public bool IsQuickButton { get; set; } = false;
    public int QuickButtonOrder { get; set; } = 0;
}
