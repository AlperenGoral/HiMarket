using HiMarket.Domain.Enums;

namespace HiMarket.Domain.Entities;

public class User : BaseEntity
{
    public string FullName { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public string PasswordHash { get; set; } = string.Empty;
    public string PinCode { get; set; } = string.Empty;
    public UserRole Role { get; set; } = UserRole.Cashier;
    public DateTime? LastLoginAt { get; set; }
}
