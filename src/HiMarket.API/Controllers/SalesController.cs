using System.Security.Claims;
using HiMarket.Application.DTOs;
using HiMarket.Application.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace HiMarket.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class SalesController : ControllerBase
{
    private readonly ISaleService _saleService;

    public SalesController(ISaleService saleService)
    {
        _saleService = saleService;
    }

    [HttpPost]
    public async Task<IActionResult> ProcessSale([FromBody] CreateSaleDto dto, [FromQuery] int cashierId = 1)
    {
        var claimId = User.FindFirstValue(ClaimTypes.NameIdentifier);
        if (int.TryParse(claimId, out int userId)) cashierId = userId;

        try
        {
            var sale = await _saleService.ProcessSaleAsync(cashierId, dto);
            return Ok(sale);
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(new { message = ex.Message });
        }
    }

    [HttpGet("receipt/{receiptNumber}")]
    public async Task<IActionResult> GetByReceipt(string receiptNumber)
    {
        var sale = await _saleService.GetSaleByReceiptNumberAsync(receiptNumber);
        if (sale == null)
            return NotFound(new { message = "Fiş numarası bulunamadı!" });

        return Ok(sale);
    }

    [HttpPost("{id:int}/cancel")]
    public async Task<IActionResult> CancelSale(int id, [FromQuery] string reason = "Müşteri vazgeçti", [FromQuery] int supervisorId = 1)
    {
        var claimId = User.FindFirstValue(ClaimTypes.NameIdentifier);
        if (int.TryParse(claimId, out int userId)) supervisorId = userId;

        var success = await _saleService.CancelSaleAsync(id, supervisorId, reason);
        if (!success)
            return BadRequest(new { message = "Satış iptal edilemedi veya zaten iptal edilmiş." });

        return Ok(new { message = "Satış başarıyla iptal edildi ve stoklar iade edildi." });
    }
}
