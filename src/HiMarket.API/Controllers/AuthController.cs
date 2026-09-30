using HiMarket.Application.DTOs;
using HiMarket.Application.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace HiMarket.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AuthController : ControllerBase
{
    private readonly IAuthService _authService;

    public AuthController(IAuthService authService)
    {
        _authService = authService;
    }

    [HttpPost("login")]
    public async Task<IActionResult> Login([FromBody] LoginRequestDto request)
    {
        var result = await _authService.LoginAsync(request);
        if (result == null)
            return Unauthorized(new { message = "E-posta veya şifre hatalı!" });

        return Ok(result);
    }

    [HttpPost("pin-login")]
    public async Task<IActionResult> PinLogin([FromBody] PinLoginRequestDto request)
    {
        var result = await _authService.PinLoginAsync(request);
        if (result == null)
            return Unauthorized(new { message = "Kasa veya PIN kodu geçersiz!" });

        return Ok(result);
    }
}
