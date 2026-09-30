namespace HiMarket.Application.DTOs;

public class ProductDto
{
    public int Id { get; set; }
    public string Barcode { get; set; } = string.Empty;
    public string? SecondaryBarcode { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? ImageUrl { get; set; }

    public int CategoryId { get; set; }
    public string CategoryName { get; set; } = string.Empty;

    public decimal BuyPrice { get; set; }
    public decimal SellPrice { get; set; }
    public decimal VatRate { get; set; }

    public bool IsWeighted { get; set; }
    public string Unit { get; set; } = "Adet";

    public decimal StockQuantity { get; set; }
    public decimal MinStockLevel { get; set; }

    public bool IsQuickButton { get; set; }
    public int QuickButtonOrder { get; set; }
}

public class CreateProductDto
{
    public string Barcode { get; set; } = string.Empty;
    public string? SecondaryBarcode { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? ImageUrl { get; set; }

    public int CategoryId { get; set; }
    public decimal BuyPrice { get; set; }
    public decimal SellPrice { get; set; }
    public decimal VatRate { get; set; } = 10;

    public bool IsWeighted { get; set; }
    public string Unit { get; set; } = "Adet";

    public decimal StockQuantity { get; set; }
    public decimal MinStockLevel { get; set; } = 5;

    public bool IsQuickButton { get; set; }
    public int QuickButtonOrder { get; set; }
}

public class BarcodeSearchResultDto
{
    public ProductDto Product { get; set; } = null!;
    public decimal Quantity { get; set; } = 1.0m;
    public bool IsWeightedBarcode { get; set; } = false;
}
