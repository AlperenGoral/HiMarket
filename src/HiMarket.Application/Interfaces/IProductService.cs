using HiMarket.Application.DTOs;

namespace HiMarket.Application.Interfaces;

public interface IProductService
{
    Task<List<ProductDto>> GetAllProductsAsync();
    Task<ProductDto?> GetProductByIdAsync(int id);
    Task<BarcodeSearchResultDto?> SearchByBarcodeAsync(string barcode);
    Task<List<ProductDto>> GetQuickButtonsAsync();
    Task<List<ProductDto>> GetByCategoryAsync(int categoryId);
    Task<ProductDto> CreateProductAsync(CreateProductDto dto);
    Task<ProductDto?> UpdateProductAsync(int id, CreateProductDto dto);
    Task<bool> DeleteProductAsync(int id);
}
