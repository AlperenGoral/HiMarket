namespace HiMarket.Domain.Entities;

public class CashRegister : BaseEntity
{
    public string Name { get; set; } = string.Empty;
    public string RegisterCode { get; set; } = string.Empty;
    public int? CurrentShiftId { get; set; }
    public Shift? CurrentShift { get; set; }
}
