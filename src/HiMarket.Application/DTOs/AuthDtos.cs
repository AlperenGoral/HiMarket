namespace HiMarket.Application.DTOs;

public record LoginRequestDto(string Email, string Password);

public record PinLoginRequestDto(string RegisterCode, string PinCode);

public record AuthResponseDto(
    string Token,
    int UserId,
    string FullName,
    string Email,
    string Role,
    int? ActiveShiftId,
    int? ActiveRegisterId
);
