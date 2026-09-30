using System.Security.Claims;
using HiMarket.Application.DTOs;
using HiMarket.Application.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace HiMarket.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class ShiftsController : ControllerBase
{
    private readonly IShiftService _shiftService;

    public ShiftsController(IShiftService shiftService)
    {
        _shiftService = shiftService;
    }

    [HttpPost("open")]
    public async Task<IActionResult> OpenShift([FromBody] OpenShiftDto dto, [FromQuery] int cashierId = 1)
    {
        // Extract cashierId from user claims if authenticated, default to query param/1 for simplicity
        var claimId = User.FindFirstValue(ClaimTypes.NameIdentifier);
        if (int.TryParse(claimId, out int userId)) cashierId = userId;

        var shift = await _shiftService.OpenShiftAsync(cashierId, dto);
        return Ok(shift);
    }

    [HttpPost("close")]
    public async Task<IActionResult> CloseShift([FromBody] CloseShiftDto dto)
    {
        var shift = await _shiftService.CloseShiftAsync(dto);
        if (shift == null)
            return BadRequest(new { message = "Vardiya bulunamadı veya zaten kapatılmış!" });

        return Ok(shift);
    }

    [HttpGet("register/{registerId:int}/active")]
    public async Task<IActionResult> GetActiveShift(int registerId)
    {
        var shift = await _shiftService.GetActiveShiftByRegisterIdAsync(registerId);
        if (shift == null)
            return NotFound(new { message = "Bu kasa için aktif vardiya yok." });

        return Ok(shift);
    }

    [HttpGet("{id:int}")]
    public async Task<IActionResult> GetById(int id)
    {
        var shift = await _shiftService.GetShiftByIdAsync(id);
        if (shift == null)
            return NotFound(new { message = "Vardiya bulunamadı." });

        return Ok(shift);
    }
}
