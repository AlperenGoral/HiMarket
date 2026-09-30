using HiMarket.Application.DTOs;

namespace HiMarket.Application.Interfaces;

public interface IShiftService
{
    Task<ShiftDto> OpenShiftAsync(int cashierId, OpenShiftDto dto);
    Task<ShiftDto?> CloseShiftAsync(CloseShiftDto dto);
    Task<ShiftDto?> GetActiveShiftByRegisterIdAsync(int registerId);
    Task<ShiftDto?> GetShiftByIdAsync(int shiftId);
}
