using HiMarket.Application.DTOs;

namespace HiMarket.Application.Interfaces;

public interface IAuthService
{
    Task<AuthResponseDto?> LoginAsync(LoginRequestDto request);
    Task<AuthResponseDto?> PinLoginAsync(PinLoginRequestDto request);
}
