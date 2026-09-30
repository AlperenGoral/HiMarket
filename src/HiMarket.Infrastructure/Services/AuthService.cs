using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using HiMarket.Application.DTOs;
using HiMarket.Application.Interfaces;
using HiMarket.Domain.Entities;
using HiMarket.Infrastructure.Persistence;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.IdentityModel.Tokens;

namespace HiMarket.Infrastructure.Services;

public class AuthService : IAuthService
{
    private readonly HiMarketDbContext _context;
    private readonly IConfiguration _configuration;

    public AuthService(HiMarketDbContext context, IConfiguration configuration)
    {
        _context = context;
        _configuration = configuration;
    }

    public async Task<AuthResponseDto?> LoginAsync(LoginRequestDto request)
    {
        var user = await _context.Users
            .FirstOrDefaultAsync(u => u.Email == request.Email && u.IsActive && !u.IsDeleted);

        if (user == null || !BCrypt.Net.BCrypt.Verify(request.Password, user.PasswordHash))
            return null;

        user.LastLoginAt = DateTime.Now;
        await _context.SaveChangesAsync();

        return await GenerateAuthResponseAsync(user, null);
    }

    public async Task<AuthResponseDto?> PinLoginAsync(PinLoginRequestDto request)
    {
        var register = await _context.CashRegisters
            .FirstOrDefaultAsync(r => r.RegisterCode == request.RegisterCode && r.IsActive && !r.IsDeleted);

        if (register == null)
            return null;

        var user = await _context.Users
            .FirstOrDefaultAsync(u => u.PinCode == request.PinCode && u.IsActive && !u.IsDeleted);

        if (user == null)
            return null;

        user.LastLoginAt = DateTime.Now;
        await _context.SaveChangesAsync();

        var activeShift = await _context.Shifts
            .FirstOrDefaultAsync(s => s.CashRegisterId == register.Id && !s.IsClosed && !s.IsDeleted);

        return await GenerateAuthResponseAsync(user, register.Id, activeShift?.Id);
    }

    private Task<AuthResponseDto> GenerateAuthResponseAsync(User user, int? registerId = null, int? activeShiftId = null)
    {
        var jwtSettings = _configuration.GetSection("Jwt");
        var key = Encoding.UTF8.GetBytes(jwtSettings["Secret"] ?? "HiMarket_Secret_Key_Super_Secure_2026!");

        var claims = new List<Claim>
        {
            new(ClaimTypes.NameIdentifier, user.Id.ToString()),
            new(ClaimTypes.Name, user.FullName),
            new(ClaimTypes.Email, user.Email),
            new(ClaimTypes.Role, user.Role.ToString())
        };

        var tokenDescriptor = new SecurityTokenDescriptor
        {
            Subject = new ClaimsIdentity(claims),
            Expires = DateTime.UtcNow.AddDays(1),
            SigningCredentials = new SigningCredentials(new SymmetricSecurityKey(key), SecurityAlgorithms.HmacSha256Signature)
        };

        var tokenHandler = new JwtSecurityTokenHandler();
        var token = tokenHandler.CreateToken(tokenDescriptor);
        var tokenString = tokenHandler.WriteToken(token);

        var response = new AuthResponseDto(
            tokenString,
            user.Id,
            user.FullName,
            user.Email,
            user.Role.ToString(),
            activeShiftId,
            registerId
        );

        return Task.FromResult(response);
    }
}
