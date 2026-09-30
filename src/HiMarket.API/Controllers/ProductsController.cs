using HiMarket.Application.DTOs;
using HiMarket.Application.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace HiMarket.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class ProductsController : ControllerBase
{
    private readonly IProductService _productService;

    public ProductsController(IProductService productService)
    {
        _productService = productService;
    }

    [HttpGet]
    public async Task<IActionResult> GetAll()
    {
        var products = await _productService.GetAllProductsAsync();
        return Ok(products);
    }

    [HttpGet("quick-buttons")]
    public async Task<IActionResult> GetQuickButtons()
    {
        var products = await _productService.GetQuickButtonsAsync();
        return Ok(products);
    }

    [HttpGet("category/{categoryId:int}")]
    public async Task<IActionResult> GetByCategory(int categoryId)
    {
        var products = await _productService.GetByCategoryAsync(categoryId);
        return Ok(products);
    }

    [HttpGet("{id:int}")]
    public async Task<IActionResult> GetById(int id)
    {
        var product = await _productService.GetProductByIdAsync(id);
        if (product == null)
            return NotFound(new { message = "Ürün bulunamadı!" });

        return Ok(product);
    }

    [HttpGet("barcode/{barcode}")]
    public async Task<IActionResult> GetByBarcode(string barcode)
    {
        var scannedItem = await _productService.SearchByBarcodeAsync(barcode);
        if (scannedItem == null)
            return NotFound(new { message = "Barkod sistemde bulunamadı!" });

        return Ok(scannedItem);
    }

    [HttpPost]
    public async Task<IActionResult> Create([FromBody] CreateProductDto dto)
    {
        var product = await _productService.CreateProductAsync(dto);
        return CreatedAtAction(nameof(GetById), new { id = product.Id }, product);
    }

    [HttpPut("{id:int}")]
    public async Task<IActionResult> Update(int id, [FromBody] CreateProductDto dto)
    {
        var updated = await _productService.UpdateProductAsync(id, dto);
        if (updated == null)
            return NotFound(new { message = "Güncellenecek ürün bulunamadı!" });

        return Ok(updated);
    }

    [HttpDelete("{id:int}")]
    public async Task<IActionResult> Delete(int id)
    {
        var success = await _productService.DeleteProductAsync(id);
        if (!success)
            return NotFound(new { message = "Silinecek ürün bulunamadı!" });

        return NoContent();
    }
}
